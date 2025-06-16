# core/dashboard_home.py
"""
Enhanced dashboard home with SEC integration statistics
"""

from dash import html, dcc, Input, Output, callback
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
from plotly_integration.models import (
    LimsUpstreamSamples, LimsSampleAnalysis, LimsSecResult,
    LimsProjectInformation, Report
)
from ..shared.styles.common_styles import PAGE_CONTENT_STYLE, ICONS


def get_enhanced_dashboard_stats():
    """Get comprehensive dashboard statistics including SEC analysis"""
    try:
        # Basic FB sample counts
        total_fb_samples = LimsUpstreamSamples.objects.filter(sample_type=2).count()

        # Recent samples (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_samples = LimsUpstreamSamples.objects.filter(
            sample_type=2,
            harvest_date__gte=thirty_days_ago.date()
        ).count()

        # SEC Analysis Statistics
        # Total samples with analysis records
        samples_with_analysis = LimsSampleAnalysis.objects.filter(
            sample_type=2
        ).count()

        # Samples with completed SEC results
        samples_with_sec = LimsSampleAnalysis.objects.filter(
            sample_type=2,
            sec_result__isnull=False
        ).count()

        # Samples with analysis but pending SEC
        samples_sec_pending = samples_with_analysis - samples_with_sec

        # Recent SEC analyses (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        recent_sec_analyses = LimsSecResult.objects.filter(
            created_at__gte=week_ago
        ).count()

        # SEC Reports count
        sec_reports = Report.objects.filter(analysis_type=1).count()

        # Sample set statistics
        from collections import defaultdict
        fb_samples = LimsUpstreamSamples.objects.filter(sample_type=2)
        grouped = defaultdict(list)

        for sample in fb_samples:
            key = (sample.project, sample.sip_number, sample.development_stage)
            grouped[key].append(sample.sample_number)

        total_sample_sets = len(grouped)

        return {
            'total_samples': total_fb_samples,
            'recent_samples': recent_samples,
            'samples_with_sec': samples_with_sec,
            'samples_sec_pending': samples_sec_pending,
            'recent_sec_analyses': recent_sec_analyses,
            'sec_reports': sec_reports,
            'total_sample_sets': total_sample_sets,
            'samples_with_analysis': samples_with_analysis
        }

    except Exception as e:
        print(f"Error getting dashboard stats: {e}")
        return {
            'total_samples': 0,
            'recent_samples': 0,
            'samples_with_sec': 0,
            'samples_sec_pending': 0,
            'recent_sec_analyses': 0,
            'sec_reports': 0,
            'total_sample_sets': 0,
            'samples_with_analysis': 0
        }


def create_stats_card(title, value, subtitle, color, icon, href=None):
    """Create a statistics card with optional navigation"""
    card_content = dbc.CardBody([
        html.Div([
            html.Div([
                html.H3(str(value), className="text-primary mb-0"),
                html.P(title, className="text-muted mb-0"),
                html.Small(subtitle, className="text-muted")
            ], className="flex-grow-1"),
            html.Div([
                html.I(className=f"fas {icon} fa-2x text-{color}")
            ], className="align-self-center")
        ], className="d-flex")
    ])

    card = dbc.Card(card_content, className="shadow-sm h-100")

    if href:
        return html.A(card, href=href, className="text-decoration-none")
    return card


def create_quick_actions_section():
    """Create quick actions section"""
    return dbc.Card([
        dbc.CardHeader([
            html.H5("⚡ Quick Actions", className="mb-0")
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Button([
                        html.I(className=f"fas {ICONS['sample_sets']} me-2"),
                        "View Sample Sets"
                    ], color="primary", href="/fb-samples/sets", size="lg",
                        className="w-100 mb-2")
                ], md=6),
                dbc.Col([
                    dbc.Button([
                        html.I(className=f"fas {ICONS['sec']} me-2"),
                        "SEC Analytics"
                    ], color="info", href="/sec/dashboard", size="lg",
                        className="w-100 mb-2")
                ], md=6),
                dbc.Col([
                    dbc.Button([
                        html.I(className=f"fas {ICONS['add']} me-2"),
                        "Add FB Samples"
                    ], color="success", href="/fb-samples/create", size="lg",
                        className="w-100 mb-2")
                ], md=6),
                dbc.Col([
                    dbc.Button([
                        html.I(className=f"fas {ICONS['samples']} me-2"),
                        "View All Samples"
                    ], color="outline-primary", href="/fb-samples/view",
                        size="lg", className="w-100 mb-2")
                ], md=6)
            ])
        ])
    ])


def create_sec_status_overview():
    """Create SEC analysis status overview"""
    return dbc.Card([
        dbc.CardHeader([
            html.H5("📊 SEC Analysis Status", className="mb-0")
        ]),
        dbc.CardBody([
            html.Div(id="sec-status-content"),
            html.Hr(),
            dbc.Button([
                html.I(className=f"fas {ICONS['analytics']} me-2"),
                "View SEC Dashboard"
            ], href="/sec/dashboard", color="outline-info", size="sm")
        ])
    ])


def create_recent_activity_section():
    """Create recent activity section"""
    return dbc.Card([
        dbc.CardHeader([
            html.H5("📈 Recent Activity", className="mb-0")
        ]),
        dbc.CardBody([
            html.Div(id="recent-activity-content"),
            dcc.Interval(
                id="activity-refresh-interval",
                interval=30000,  # Update every 30 seconds
                n_intervals=0
            )
        ])
    ])


def create_dashboard_home_layout():
    """Create the main dashboard home layout"""
    stats = get_enhanced_dashboard_stats()

    return html.Div([
        # Header
        dbc.Row([
            dbc.Col([
                html.H2("🧬 CLD Analytics Dashboard", className="text-primary mb-1"),
                html.P("Cell Line Development - FB Sample Management & SEC Analytics",
                       className="text-muted mb-4")
            ])
        ]),

        # Statistics Cards Row 1
        dbc.Row([
            dbc.Col([
                create_stats_card(
                    "Total FB Samples",
                    stats['total_samples'],
                    "All time",
                    "primary",
                    ICONS['samples'],
                    href="/fb-samples/view"
                )
            ], md=3),
            dbc.Col([
                create_stats_card(
                    "Sample Sets",
                    stats['total_sample_sets'],
                    "Grouped sets",
                    "info",
                    ICONS['sample_sets'],
                    href="/fb-samples/sets"
                )
            ], md=3),
            dbc.Col([
                create_stats_card(
                    "Recent Samples",
                    stats['recent_samples'],
                    "Last 30 days",
                    "success",
                    ICONS['add']
                )
            ], md=3),
            dbc.Col([
                create_stats_card(
                    "SEC Reports",
                    stats['sec_reports'],
                    "Generated reports",
                    "warning",
                    ICONS['reports'],
                    href="/sec/reports"
                )
            ], md=3)
        ], className="mb-4"),

        # Statistics Cards Row 2 - SEC Focus
        dbc.Row([
            dbc.Col([
                create_stats_card(
                    "SEC Complete",
                    stats['samples_with_sec'],
                    "Samples analyzed",
                    "success",
                    ICONS['complete'],
                    href="/sec/dashboard"
                )
            ], md=3),
            dbc.Col([
                create_stats_card(
                    "SEC Pending",
                    stats['samples_sec_pending'],
                    "Analysis requested",
                    "warning",
                    ICONS['pending'],
                    href="/sec/sample-sets"
                )
            ], md=3),
            dbc.Col([
                create_stats_card(
                    "Recent SEC",
                    stats['recent_sec_analyses'],
                    "Last 7 days",
                    "info",
                    ICONS['sec']
                )
            ], md=3),
            dbc.Col([
                create_stats_card(
                    "Analysis Records",
                    stats['samples_with_analysis'],
                    "LIMS records",
                    "secondary",
                    ICONS['analytics']
                )
            ], md=3)
        ], className="mb-4"),

        # Main Content Row
        dbc.Row([
            # Quick Actions
            dbc.Col([
                create_quick_actions_section()
            ], md=8),

            # Recent Activity
            dbc.Col([
                create_recent_activity_section()
            ], md=4)
        ], className="mb-4"),

        # SEC Status Overview
        dbc.Row([
            dbc.Col([
                create_sec_status_overview()
            ], md=12)
        ])

    ], style=PAGE_CONTENT_STYLE)


def create_dashboard_callbacks(app):
    """Create callbacks for dashboard home page"""

    @app.callback(
        Output("sec-status-content", "children"),
        Input("url", "pathname"),
        prevent_initial_call=True
    )
    def update_sec_status_overview(pathname):
        """Update SEC status overview"""
        if pathname != "/":
            return ""

        try:
            stats = get_enhanced_dashboard_stats()

            # Calculate percentages
            total_samples = stats['total_samples']
            if total_samples == 0:
                return html.P("No FB samples found.", className="text-muted")

            sec_complete_pct = round((stats['samples_with_sec'] / total_samples) * 100, 1)
            analysis_requested_pct = round((stats['samples_with_analysis'] / total_samples) * 100, 1)

            return [
                dbc.Row([
                    dbc.Col([
                        html.H6("SEC Analysis Coverage", className="text-primary"),
                        dbc.Progress(
                            value=sec_complete_pct,
                            label=f"{sec_complete_pct}%",
                            color="success",
                            className="mb-2"
                        ),
                        html.Small(f"{stats['samples_with_sec']} of {total_samples} samples analyzed")
                    ], md=6),
                    dbc.Col([
                        html.H6("Analysis Requests", className="text-info"),
                        dbc.Progress(
                            value=analysis_requested_pct,
                            label=f"{analysis_requested_pct}%",
                            color="info",
                            className="mb-2"
                        ),
                        html.Small(f"{stats['samples_with_analysis']} samples have LIMS records")
                    ], md=6)
                ])
            ]

        except Exception as e:
            return dbc.Alert(f"Error loading SEC status: {e}", color="warning")

    @app.callback(
        Output("recent-activity-content", "children"),
        Input("activity-refresh-interval", "n_intervals"),
        prevent_initial_call=True
    )
    def update_recent_activity(n_intervals):
        """Update recent activity feed"""
        try:
            # Get recent activities
            recent_items = []

            # Recent SEC analyses
            week_ago = datetime.now() - timedelta(days=7)
            recent_sec = LimsSecResult.objects.filter(
                created_at__gte=week_ago
            ).order_by('-created_at')[:3]

            for sec_result in recent_sec:
                sample_id = sec_result.sample_id.sample_id
                created = sec_result.created_at.strftime("%m/%d %H:%M")
                recent_items.append(
                    html.P([
                        html.I(className="fas fa-microscope text-success me-2"),
                        f"SEC analysis completed for {sample_id}",
                        html.Small(f" - {created}", className="text-muted ms-2")
                    ], className="small mb-1")
                )

            # Recent samples
            recent_samples = LimsUpstreamSamples.objects.filter(
                sample_type=2,
                harvest_date__gte=week_ago.date()
            ).order_by('-harvest_date')[:2]

            for sample in recent_samples:
                harvest_date = sample.harvest_date.strftime("%m/%d") if sample.harvest_date else "Unknown"
                recent_items.append(
                    html.P([
                        html.I(className="fas fa-plus-circle text-primary me-2"),
                        f"New FB sample: FB{sample.sample_number}",
                        html.Small(f" - {harvest_date}", className="text-muted ms-2")
                    ], className="small mb-1")
                )

            if not recent_items:
                recent_items = [
                    html.P([
                        html.I(className="fas fa-info-circle text-info me-2"),
                        "No recent activity"
                    ], className="small text-muted")
                ]

            return recent_items

        except Exception as e:
            return [html.P(f"Error loading activity: {e}", className="small text-danger")]