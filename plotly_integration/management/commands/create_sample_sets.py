# plotly_integration/management/commands/create_sample_sets.py

from django.core.management.base import BaseCommand
from django.db import transaction
from plotly_integration.models import (
    LimsUpstreamSamples,
    LimsSampleAnalysis,
    LimsSampleSet,
    LimsSampleSetMembership
)


class Command(BaseCommand):
    help = 'Create sample sets from existing FB samples'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run the command without making changes to the database',
        )
        parser.add_argument(
            '--project',
            type=str,
            help='Only process samples from a specific project',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        project_filter = options['project']
        verbose = options['verbose']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Get all unique combinations of project, sip, stage for FB samples
        query = LimsUpstreamSamples.objects.filter(sample_type=2)  # FB = 2

        if project_filter:
            query = query.filter(project=project_filter)
            self.stdout.write(f"Filtering for project: {project_filter}")

        # Get unique combinations
        unique_sets = query.values(
            'project', 'sip_number', 'development_stage'
        ).distinct().order_by('project', 'sip_number', 'development_stage')

        self.stdout.write(f"Found {unique_sets.count()} unique sample set combinations")

        created_count = 0
        updated_count = 0
        error_count = 0

        with transaction.atomic():
            for set_data in unique_sets:
                try:
                    # Skip if all key fields are None/empty
                    if not set_data['project']:
                        if verbose:
                            self.stdout.write(self.style.WARNING(
                                "Skipping set with no project"
                            ))
                        continue

                    # Generate sample set name
                    set_name_parts = [set_data['project']]
                    if set_data['sip_number']:
                        set_name_parts.append(f"SIP{set_data['sip_number']}")
                    if set_data['development_stage']:
                        set_name_parts.append(set_data['development_stage'])

                    set_name = "_".join(set_name_parts)

                    if verbose:
                        self.stdout.write(f"Processing: {set_name}")

                    if not dry_run:
                        # Create or get sample set
                        sample_set, created = LimsSampleSet.objects.get_or_create(
                            project_id=set_data['project'],
                            sip_number=set_data['sip_number'] or "",
                            development_stage=set_data['development_stage'] or "",
                            defaults={
                                'set_name': set_name,
                                'created_by': 'migration'
                            }
                        )

                        if created:
                            created_count += 1
                            self.stdout.write(self.style.SUCCESS(f"✅ Created: {set_name}"))
                        else:
                            updated_count += 1
                            if verbose:
                                self.stdout.write(f"  Already exists: {set_name}")

                        # Get all samples for this set
                        samples = LimsUpstreamSamples.objects.filter(
                            project=set_data['project'],
                            sample_type=2
                        )

                        # Apply additional filters if they exist
                        if set_data['sip_number'] is not None:
                            samples = samples.filter(sip_number=set_data['sip_number'])
                        else:
                            samples = samples.filter(sip_number__isnull=True)

                        if set_data['development_stage'] is not None:
                            samples = samples.filter(development_stage=set_data['development_stage'])
                        else:
                            samples = samples.filter(development_stage__isnull=True)

                        # Add members
                        membership_count = 0
                        for sample in samples:
                            try:
                                # Get or create the corresponding LimsSampleAnalysis record
                                sample_analysis, _ = LimsSampleAnalysis.objects.get_or_create(
                                    sample_id=f'FB{sample.sample_number}',
                                    sample_type=2,
                                    defaults={
                                        'project_id': sample.project,
                                        'sample_date': sample.harvest_date,
                                        'analyst': sample.analyst or '',
                                        'notes': sample.note or ''
                                    }
                                )

                                # Create membership
                                _, membership_created = LimsSampleSetMembership.objects.get_or_create(
                                    sample_set=sample_set,
                                    sample=sample_analysis
                                )

                                if membership_created:
                                    membership_count += 1

                            except Exception as e:
                                self.stdout.write(self.style.WARNING(
                                    f"  Warning: Could not add sample FB{sample.sample_number}: {e}"
                                ))

                        # Update sample count
                        sample_set.sample_count = sample_set.members.count()
                        sample_set.save()

                        if verbose or created:
                            self.stdout.write(
                                f"  Added {membership_count} new members, "
                                f"total: {sample_set.sample_count} samples"
                            )
                    else:
                        # Dry run - just show what would be created
                        sample_count = LimsUpstreamSamples.objects.filter(
                            project=set_data['project'],
                            sip_number=set_data['sip_number'],
                            development_stage=set_data['development_stage'],
                            sample_type=2
                        ).count()

                        self.stdout.write(
                            f"Would create: {set_name} with {sample_count} samples"
                        )

                except Exception as e:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(
                        f"❌ Error processing {set_data}: {str(e)}"
                    ))
                    if not dry_run:
                        raise  # Re-raise to trigger rollback

        # Summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("SUMMARY"))
        self.stdout.write(f"✅ Created: {created_count} new sample sets")
        self.stdout.write(f"📝 Updated: {updated_count} existing sample sets")
        if error_count:
            self.stdout.write(self.style.ERROR(f"❌ Errors: {error_count}"))

        if dry_run:
            self.stdout.write(self.style.WARNING("\nDRY RUN COMPLETE - No changes were made"))