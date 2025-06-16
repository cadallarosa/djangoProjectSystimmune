from plotly_integration.models import LimsUpstreamSamples, LimsSampleAnalysis

# Map sample_type to prefix
sample_types = {
    1: "FB",  # Fed-batch
    2: "UP",  # Upstream
}

created, skipped = 0, 0

# Query both types at once
all_samples = LimsUpstreamSamples.objects.filter(sample_type__in=sample_types.keys())

for up in all_samples:
    if not up.sample_number:
        continue

    prefix = sample_types.get(up.sample_type)
    full_sample_id = f"{prefix}{up.sample_number}"

    # Skip if already exists
    if LimsSampleAnalysis.objects.filter(sample_id=full_sample_id).exists():
        skipped += 1
        continue

    LimsSampleAnalysis.objects.create(
        sample_id=full_sample_id,
        sample_date=up.harvest_date,
        project_id=up.project,
        description=up.cell_line or "",
        notes=up.note or "",
        up=up  # or `up_id=up.id` if you're using the ID directly
    )
    created += 1

print(f"✅ Created: {created}, Skipped: {skipped}")


from plotly_integration.models import LimsSampleAnalysis

# Loop through all LimsSampleAnalysis samples
updated_count = 0
skipped_count = 0

for sample in LimsSampleAnalysis.objects.all():
    if not sample.sample_id:
        continue

    # Check sample ID prefix and update sample_type
    if sample.sample_id.startswith("PD"):
        new_sample_type = 3  # PD
    elif sample.sample_id.startswith("UP"):
        new_sample_type = 1  # UP
    elif sample.sample_id.startswith("FB"):
        new_sample_type = 2  # FB
    else:
        skipped_count += 1
        continue  # Skip if the sample ID doesn't match any known prefixes

    # Update the sample type if it is different
    if sample.sample_type != new_sample_type:
        sample.sample_type = new_sample_type
        sample.save()
        updated_count += 1
    else:
        skipped_count += 1

# Output result
print(f"✅ Updated: {updated_count} | ❌ Skipped: {skipped_count}")