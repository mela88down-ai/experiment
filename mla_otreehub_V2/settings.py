from os import environ

SESSION_CONFIGS = [
    dict(
        name='mla_main',
        display_name='MLA – design principal fréquence × saillance',
        num_demo_participants=80,
        app_sequence=['mla_experiment'],
        pilot=False,
    ),

    dict(
        name='mla_debug',
        display_name='MLA – mode test visuel A/B/C/D',
        num_demo_participants=8,
        app_sequence=['mla_experiment'],
        pilot=False,
        debug_visual=True,
    ),
    dict(
        name='mla_pilot',
        display_name='MLA – pilote validation manipulation',
        num_demo_participants=10,
        app_sequence=['mla_experiment'],
        pilot=True,
    ),
]

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=0.00,
    participation_fee=0.00,
    doc='Design expérimental mémoire MLA : fréquence du feedback × saillance des pertes.',
)

PARTICIPANT_FIELDS = [
    'treatment',
    'condition_index',
    'salience_order',
    'cfc_score',
    'loss_aversion_index',
    'lottery_refusals',
]

SESSION_FIELDS = []

LANGUAGE_CODE = 'fr'
REAL_WORLD_CURRENCY_CODE = 'EUR'
USE_POINTS = False

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD', 'admin')

DEMO_PAGE_INTRO_HTML = """
<h4>MLA – Design expérimental</h4>
<p>Session principale : 80 participants, 4 conditions A/B/C/D.</p>
<p>Session pilote : 10 participants, conditions A et D seulement, avec questions de validation.</p>
"""

SECRET_KEY = environ.get('OTREE_SECRET_KEY', 'change-this-before-deployment')
INSTALLED_APPS = ['otree']
