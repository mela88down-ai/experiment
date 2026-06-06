from otree.api import *
import random


doc = """
Expérience oTree pour le mémoire de finance comportementale :
Myopic Loss Aversion, fréquence du feedback, saillance attentionnelle/perceptive
et saillance économique des pertes.
"""


class C(BaseConstants):
    NAME_IN_URL = 'mla_experiment'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 20

    ENDOWMENT = 10.0
    BLOCK_SIZE = 5

    BASE_GAIN_MULT = 2.5
    BASE_LOSS_MULT = 1.0
    ECON_GAIN_MULT = 6.5
    ECON_LOSS_MULT = 3.0

    LIKERT_CHOICES = [
        [1, '1'],
        [2, '2'],
        [3, '3'],
        [4, '4'],
        [5, '5'],
        [6, '6'],
        [7, '7'],
    ]

    CFC_REVERSED_ITEMS = [3, 4, 5, 9, 10, 11, 12]


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


def _round2(x):
    if x is None:
        return None
    return round(float(x), 2)


def get_treatment_for_player(player):
    """
    Main: balanced by modulo over A/B/C/D.
    With 80 participants, this gives exactly 20 by condition.
    Pilot: A/D only, alternating.
    """
    pid = player.participant.id_in_session
    if player.session.config.get('pilot', False):
        return 'A' if pid % 2 == 1 else 'D'
    return ['A', 'B', 'C', 'D'][(pid - 1) % 4]


def get_condition_index(player, treatment):
    """
    Index inside treatment group, used for counterbalancing.
    Main: 1..20 for each condition if N=80.
    Pilot: approximate index inside A or D.
    """
    pid = player.participant.id_in_session
    if player.session.config.get('pilot', False):
        return (pid + 1) // 2
    return ((pid - 1) // 4) + 1


def get_salience_order(player, treatment):
    """
    For C/D only:
    - first half: perceptive first, economic second
    - second half: economic first, perceptive second
    """
    if treatment not in ['C', 'D']:
        return 'none'
    idx = get_condition_index(player, treatment)
    return 'perceptive_first' if idx <= 10 else 'economic_first'


def get_part_number(player):
    if get_treatment_for_player(player) in ['C', 'D']:
        return 1 if player.round_number <= 10 else 2
    return 1


def get_salience_type(player):
    treatment = get_treatment_for_player(player)
    if treatment in ['A', 'B']:
        return 'none'

    order = get_salience_order(player, treatment)
    part = get_part_number(player)

    if order == 'perceptive_first':
        return 'perceptive' if part == 1 else 'economic'
    else:
        return 'economic' if part == 1 else 'perceptive'


def is_frequent_feedback(treatment):
    return treatment in ['B', 'D']


def is_feedback_page_displayed(player):
    treatment = player.treatment or get_treatment_for_player(player)
    if is_frequent_feedback(treatment):
        return True
    return player.round_number % C.BLOCK_SIZE == 0


def current_block_start_end(player):
    end_round = player.round_number
    start_round = end_round - C.BLOCK_SIZE + 1
    return start_round, end_round


def get_payoff_multipliers(salience_type):
    if salience_type == 'economic':
        return C.ECON_GAIN_MULT, C.ECON_LOSS_MULT
    return C.BASE_GAIN_MULT, C.BASE_LOSS_MULT


def setup_player_round(player):
    treatment = get_treatment_for_player(player)
    condition_index = get_condition_index(player, treatment)
    salience_order = get_salience_order(player, treatment)
    salience_type = get_salience_type(player)
    gain_mult, loss_mult = get_payoff_multipliers(salience_type)

    player.treatment = treatment
    player.condition_index = condition_index
    player.salience_order = salience_order
    player.frequent_feedback = 1 if is_frequent_feedback(treatment) else 0
    player.feedback_mode = 'frequent' if player.frequent_feedback else 'aggregate'
    player.high_salience = 1 if treatment in ['C', 'D'] else 0
    player.salience_type = salience_type
    player.visual_salience = 1 if salience_type == 'perceptive' else 0
    player.economic_salience = 1 if salience_type == 'economic' else 0
    player.part_number = get_part_number(player)
    player.period_in_part = ((player.round_number - 1) % 10) + 1 if treatment in ['C', 'D'] else player.round_number
    player.block_number = ((player.round_number - 1) // C.BLOCK_SIZE) + 1
    player.block_in_part = ((player.period_in_part - 1) // C.BLOCK_SIZE) + 1
    player.gain_multiplier = gain_mult
    player.loss_multiplier = loss_mult

    if 'cfc_score' in player.participant.vars:
        player.cfc_score = player.participant.vars['cfc_score']


def creating_session(subsession):
    for player in subsession.get_players():
        setup_player_round(player)
        if subsession.round_number == 1:
            player.participant.vars['treatment'] = player.treatment
            player.participant.vars['condition_index'] = player.condition_index
            player.participant.vars['salience_order'] = player.salience_order


class Player(BasePlayer):
    # -------------------------
    # Consent
    # -------------------------
    consent = models.BooleanField(
        label="Je confirme avoir lu les informations et j'accepte de participer à cette étude.",
        blank=False,
    )

    # -------------------------
    # CFC-14
    # -------------------------
    cfc_1 = models.IntegerField(
        label="1. J’imagine comment les choses seront dans le futur et j’essaie de les influencer par mon comportement quotidien.",
        choices=C.LIKERT_CHOICES,
        widget=widgets.RadioSelect,
    )

    cfc_2 = models.IntegerField(
        label="2. J’agis souvent pour atteindre des buts qui ne se concrétiseront que dans plusieurs années.",
        choices=C.LIKERT_CHOICES,
        widget=widgets.RadioSelect,
    )

    cfc_3 = models.IntegerField(
        label="3. J’agis uniquement pour satisfaire mes préoccupations immédiates, pensant que le futur s’arrangera de lui-même.",
        choices=C.LIKERT_CHOICES,
        widget=widgets.RadioSelect,
    )

    cfc_4 = models.IntegerField(
        label="4. Mon comportement est influencé uniquement par les conséquences immédiates de mes actions (immédiat = dans les jours ou semaines qui suivent).",
        choices=C.LIKERT_CHOICES,
        widget=widgets.RadioSelect,
    )

    cfc_5 = models.IntegerField(
        label="5. La satisfaction de mes envies immédiates a une grande influence sur mes comportements ou sur les décisions que je prends.",
        choices=C.LIKERT_CHOICES,
        widget=widgets.RadioSelect,
    )

    cfc_6 = models.IntegerField(
        label="6. Je suis prêt(e) à sacrifier mon bonheur ou bien-être immédiat pour atteindre des objectifs futurs.",
        choices=C.LIKERT_CHOICES,
        widget=widgets.RadioSelect,
    )

    cfc_7 = models.IntegerField(
        label="7. Je pense qu’il est important de prendre au sérieux les mises en garde contre les conséquences négatives de mes actes, même si celles-ci ne surviendront pas avant plusieurs années.",
        choices=C.LIKERT_CHOICES,
        widget=widgets.RadioSelect,
    )

    cfc_8 = models.IntegerField(
        label="8. Je pense qu’il est plus important de réaliser un comportement qui aura des conséquences futures importantes, qu’un comportement ayant des conséquences immédiates mais de moindre importance.",
        choices=C.LIKERT_CHOICES,
        widget=widgets.RadioSelect,
    )

    cfc_9 = models.IntegerField(
        label="9. Je ne tiens généralement pas compte des mises en garde contre d’éventuels futurs problèmes, car je pense que ceux-ci seront résolus avant d’atteindre un niveau critique.",
        choices=C.LIKERT_CHOICES,
        widget=widgets.RadioSelect,
    )

    cfc_10 = models.IntegerField(
        label="10. Je pense que se sacrifier aujourd’hui n’est généralement pas nécessaire puisque les problèmes futurs pourront être traités plus tard.",
        choices=C.LIKERT_CHOICES,
        widget=widgets.RadioSelect,
    )

    cfc_11 = models.IntegerField(
        label="11. J’agis uniquement pour répondre à des préoccupations immédiates, pensant que je m’occuperai plus tard des futurs problèmes qui peuvent survenir.",
        choices=C.LIKERT_CHOICES,
        widget=widgets.RadioSelect,
    )

    cfc_12 = models.IntegerField(
        label="12. Puisque mes actions quotidiennes ont des résultats immédiats, elles sont plus importantes pour moi qu’un comportement ayant des conséquences lointaines.",
        choices=C.LIKERT_CHOICES,
        widget=widgets.RadioSelect,
    )

    cfc_13 = models.IntegerField(
        label="13. Quand je prends une décision, je réfléchis à la façon dont elle pourrait m’affecter dans le futur.",
        choices=C.LIKERT_CHOICES,
        widget=widgets.RadioSelect,
    )

    cfc_14 = models.IntegerField(
        label="14. Mon comportement est en général influencé par ses conséquences futures.",
        choices=C.LIKERT_CHOICES,
        widget=widgets.RadioSelect,
    )

    cfc_score = models.FloatField(blank=True)
    cfc_raw_score = models.FloatField(blank=True)

    # -------------------------
    # Treatment/design fields
    # -------------------------
    treatment = models.StringField(blank=True)
    condition_index = models.IntegerField(blank=True)
    salience_order = models.StringField(blank=True)
    frequent_feedback = models.IntegerField(blank=True)
    feedback_mode = models.StringField(blank=True)
    high_salience = models.IntegerField(blank=True)
    salience_type = models.StringField(blank=True)  # none / perceptive / economic
    visual_salience = models.IntegerField(blank=True)
    economic_salience = models.IntegerField(blank=True)
    part_number = models.IntegerField(blank=True)
    period_in_part = models.IntegerField(blank=True)
    block_number = models.IntegerField(blank=True)
    block_in_part = models.IntegerField(blank=True)
    gain_multiplier = models.FloatField(blank=True)
    loss_multiplier = models.FloatField(blank=True)

    # -------------------------
    # Investment task
    # -------------------------
    investment = models.FloatField(
        label="Montant investi dans l'actif risqué, entre 0 € et 10 €",
        min=0,
        max=10,
    )

    decision_ms = models.IntegerField(blank=True, initial=0)

    draw_favorable = models.BooleanField(blank=True)
    net_result = models.FloatField(blank=True)
    period_score = models.FloatField(blank=True)

    block_score = models.FloatField(blank=True)
    block_net_result = models.FloatField(blank=True)
    block_total_investment = models.FloatField(blank=True)

    loss_t_minus_1 = models.IntegerField(blank=True, initial=0)
    risk_share = models.FloatField(blank=True)

    # -------------------------
    # Pilot checks
    # -------------------------
    salience_check = models.IntegerField(
        label='Dans quelle mesure les pertes vous ont-elles paru visibles ou marquantes ?',
        choices=[
            [1, '1 - Pas du tout'],
            [2, '2'],
            [3, '3'],
            [4, '4'],
            [5, '5'],
            [6, '6'],
            [7, '7 - Très fortement'],
        ],
        widget=widgets.RadioSelect,
        blank=True,
    )

    comprehension_check = models.StringField(
        label='Dans la règle alternative, que se passe-t-il si vous investissez 4 € et que le tirage est défavorable ?',
        choices=[
            ['correct', 'Vous perdez 3 × 4 €, donc 12 € ; le score de période est 10 − 12 = −2 €.'],
            ['wrong_base', 'Vous perdez seulement 4 €, comme dans la règle de base.'],
            ['wrong_reset', 'Vous ne pouvez plus investir aux périodes suivantes.'],
        ],
        widget=widgets.RadioSelect,
        blank=True,
    )


# -------------------------
# Helper calculations
# -------------------------

def compute_cfc_score(player):
    values = [
        player.cfc_1, player.cfc_2, player.cfc_3, player.cfc_4,
        player.cfc_5, player.cfc_6, player.cfc_7, player.cfc_8,
        player.cfc_9, player.cfc_10, player.cfc_11, player.cfc_12,
        player.cfc_13, player.cfc_14,
    ]

    raw = sum(values) / len(values)

    recoded = []
    for idx, value in enumerate(values, start=1):
        recoded.append(8 - value if idx in C.CFC_REVERSED_ITEMS else value)

    score = sum(recoded) / len(recoded)

    player.cfc_raw_score = _round2(raw)
    player.cfc_score = _round2(score)
    player.participant.vars['cfc_score'] = player.cfc_score


def compute_investment_outcome(player):
    setup_player_round(player)

    if player.round_number > 1:
        previous = player.in_round(player.round_number - 1)
        player.loss_t_minus_1 = 1 if (previous.net_result is not None and previous.net_result < 0) else 0
    else:
        player.loss_t_minus_1 = 0

    player.risk_share = _round2(player.investment / C.ENDOWMENT)

    favorable = random.random() < (1 / 3)
    player.draw_favorable = favorable

    if favorable:
        net = player.gain_multiplier * player.investment
    else:
        net = -player.loss_multiplier * player.investment

    player.net_result = _round2(net)
    player.period_score = _round2(C.ENDOWMENT + net)

    if is_feedback_page_displayed(player):
        fill_block_results(player)


def fill_block_results(player):
    if player.frequent_feedback:
        player.block_score = player.period_score
        player.block_net_result = player.net_result
        player.block_total_investment = player.investment
        return

    start, end = current_block_start_end(player)
    rounds = player.in_rounds(start, end)
    player.block_score = _round2(sum(p.period_score for p in rounds if p.period_score is not None))
    player.block_net_result = _round2(sum(p.net_result for p in rounds if p.net_result is not None))
    player.block_total_investment = _round2(sum(p.investment for p in rounds if p.investment is not None))


def final_score(player):
    return _round2(sum(p.period_score for p in player.in_all_rounds() if p.period_score is not None))


def display_amount(x):
    if x is None:
        return ''
    return f"{x:.2f}".replace('.', ',')


# -------------------------
# Pages
# -------------------------

class Consent(Page):
    form_model = 'player'
    form_fields = ['consent']

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

    @staticmethod
    def error_message(player, values):
        if not values.get('consent'):
            return "Vous devez accepter les conditions pour participer."


class CFC(Page):
    form_model = 'player'
    form_fields = [
        'cfc_1', 'cfc_2', 'cfc_3', 'cfc_4', 'cfc_5', 'cfc_6',
        'cfc_7', 'cfc_8', 'cfc_9', 'cfc_10', 'cfc_11', 'cfc_12',
        'cfc_13', 'cfc_14'
    ]

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

    @staticmethod
    def before_next_page(player, timeout_happened):
        compute_cfc_score(player)


class GeneralInstructions(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1


class TreatmentInstructions(Page):
    @staticmethod
    def is_displayed(player):
        treatment = get_treatment_for_player(player)
        if player.round_number == 1:
            return True
        return treatment in ['C', 'D'] and player.round_number == 11

    @staticmethod
    def vars_for_template(player):
        setup_player_round(player)
        treatment = player.treatment
        salience_type = player.salience_type
        is_cd = treatment in ['C', 'D']
        is_economic = salience_type == 'economic'
        is_perceptive = salience_type == 'perceptive'

        return dict(
            treatment=treatment,
            is_cd=is_cd,
            is_frequent=bool(player.frequent_feedback),
            is_aggregate=not bool(player.frequent_feedback),
            part_number=player.part_number,
            salience_type=salience_type,
            is_economic=is_economic,
            is_perceptive=is_perceptive,
            gain_multiplier=display_amount(player.gain_multiplier),
            loss_multiplier=display_amount(player.loss_multiplier),
        )


class Investment(Page):
    form_model = 'player'
    form_fields = ['investment', 'decision_ms']

    @staticmethod
    def vars_for_template(player):
        setup_player_round(player)
        return dict(
            treatment=player.treatment,
            round_number=player.round_number,
            period_in_part=player.period_in_part,
            part_number=player.part_number,
            is_cd=player.treatment in ['C', 'D'],
            salience_type=player.salience_type,
            gain_multiplier=display_amount(player.gain_multiplier),
            loss_multiplier=display_amount(player.loss_multiplier),
            endowment=display_amount(C.ENDOWMENT),
            is_economic=player.salience_type == 'economic',
        )

    @staticmethod
    def before_next_page(player, timeout_happened):
        compute_investment_outcome(player)


class Feedback(Page):
    @staticmethod
    def is_displayed(player):
        return is_feedback_page_displayed(player)

    @staticmethod
    def vars_for_template(player):
        setup_player_round(player)
        fill_block_results(player)

        is_frequent = bool(player.frequent_feedback)
        visual = player.treatment in ['C', 'D'] and player.salience_type == 'perceptive'
        debug_visual = bool(player.session.config.get('debug_visual', False))

        if is_frequent:
            shown_score = player.period_score
            shown_net = player.net_result
            shown_investment = player.investment
        else:
            shown_score = player.block_score
            shown_net = player.block_net_result
            shown_investment = player.block_total_investment

        negative = shown_net is not None and shown_net < 0
        positive = shown_net is not None and shown_net > 0

        if shown_investment and shown_investment > 0:
            pct_of_investment = _round2(100 * shown_net / shown_investment)
        else:
            pct_of_investment = None

        net_label = 'Résultat net de la période' if is_frequent else 'Résultat net du bloc'

        if is_frequent:
            if negative:
                if player.salience_type == 'economic':
                    explanation = (
                        f'Tirage défavorable : la perte correspond à {display_amount(player.loss_multiplier)} fois '
                        f'le montant investi. Le score de la période est donc 10 € plus ce résultat net négatif.'
                    )
                else:
                    explanation = (
                        'Tirage défavorable : vous perdez le montant investi. '
                        'Le score de la période est donc 10 € plus ce résultat net négatif.'
                    )
            elif positive:
                explanation = (
                    f'Tirage favorable : le gain net correspond à {display_amount(player.gain_multiplier)} fois '
                    'le montant investi. Le score de la période est donc 10 € plus ce résultat net positif.'
                )
            else:
                explanation = 'Le résultat net de cette période est nul.'
        else:
            if negative:
                explanation = (
                    'Le bloc est globalement en perte : ce résultat net correspond à la somme des résultats nets '
                    'des 5 périodes du bloc. Les résultats intermédiaires ne sont pas affichés dans cette condition.'
                )
            elif positive:
                explanation = (
                    'Le bloc est globalement en gain : ce résultat net correspond à la somme des résultats nets '
                    'des 5 périodes du bloc. Les résultats intermédiaires ne sont pas affichés dans cette condition.'
                )
            else:
                explanation = (
                    'Le résultat net du bloc est nul. Il correspond à la somme des résultats nets des 5 périodes du bloc.'
                )

        debug_rows = []
        if debug_visual:
            if is_frequent:
                debug_rounds = [player]
            else:
                start, end = current_block_start_end(player)
                debug_rounds = [p for p in player.in_rounds(start, end)]

            for p in debug_rounds:
                debug_rows.append(dict(
                    round_number=p.round_number,
                    period_in_part=p.period_in_part,
                    investment=display_amount(p.investment),
                    net=display_amount(p.net_result),
                    score=display_amount(p.period_score),
                    loss=bool(p.net_result is not None and p.net_result < 0),
                    visual_expected=bool(p.treatment in ['C', 'D'] and p.salience_type == 'perceptive'),
                    salience_type=p.salience_type,
                    treatment=p.treatment,
                ))

        return dict(
            is_frequent=is_frequent,
            is_aggregate=not is_frequent,
            visual=visual,
            negative=negative,
            positive=positive,
            score=display_amount(shown_score),
            net=display_amount(shown_net),
            net_label=net_label,
            explanation=explanation,
            pct=display_amount(pct_of_investment) if pct_of_investment is not None else None,
            block_number=player.block_number,
            block_in_part=player.block_in_part,
            round_number=player.round_number,
            treatment=player.treatment,
            salience_type=player.salience_type,
            debug_visual=debug_visual,
            debug_rows=debug_rows,
        )


class BetweenParts(Page):
    @staticmethod
    def is_displayed(player):
        return get_treatment_for_player(player) in ['C', 'D'] and player.round_number == 10


class ManipulationCheck(Page):
    form_model = 'player'
    form_fields = ['salience_check', 'comprehension_check']

    @staticmethod
    def is_displayed(player):
        return player.session.config.get('pilot', False) and player.round_number == C.NUM_ROUNDS


class FinalResults(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player):
        avg_investment = _round2(sum(p.investment for p in player.in_all_rounds()) / C.NUM_ROUNDS)
        avg_risk_share = _round2(avg_investment / C.ENDOWMENT)

        return dict(
            final_score=display_amount(final_score(player)),
            avg_investment=display_amount(avg_investment),
            avg_risk_share=display_amount(avg_risk_share),
            treatment=player.treatment,
        )


page_sequence = [
    Consent,
    CFC,
    GeneralInstructions,
    TreatmentInstructions,
    Investment,
    Feedback,
    BetweenParts,
    ManipulationCheck,
    FinalResults,
]
