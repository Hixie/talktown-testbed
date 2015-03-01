from belief import *


class Acquaintance(object):
    """One person's conception of their acquaintance with another person."""

    def __init__(self, owner, subject, preceded_by):
        """Initialize an Acquaintance object.

        @param owner: The person whom this conception of the acquaintance belongs to.
        @param subject: The other person to whom the conception pertains.
        @param preceded_by: A Kinship relationship that preceded this, if any.
        """
        self.type = 'acquaintance'
        self.owner = owner
        self.subject = subject
        self.preceded_by = preceded_by
        if preceded_by:
            preceded_by.succeeded_by = self
        self.succeeded_by = None  # May get set by a succeeding Friendship object
        self.where_they_met = self.owner.location
        self.when_they_met = self.owner.game.date
        # Set this as the primary relationship owner has with subject
        self.owner.relationships[self.subject] = self
        self.compatibility = self._init_get_compatibility()
        self.charge_increment = self._init_determine_charge_increment()
        self.charge = float(self.charge_increment)
        self.spark_increment = self._init_determine_initial_spark_increment()
        self.spark = float(self.spark_increment)
        self.form_or_build_up_mental_model()

    def _init_get_compatibility(self):
        """Determine the objective compatibility of these two people.

        From source [4]: # People with similar openness, extroversion, and agreeableness are
        more likely to become friends.
        """
        # Get absolute difference in o, e, a
        diff = (
            abs(self.owner.personality.openness_to_experience - self.subject.personality.openness_to_experience) +
            abs(self.owner.personality.extroversion - self.subject.personality.extroversion) +
            abs(self.owner.personality.agreeableness - self.subject.personality.agreeableness)
        )
        # Normalize absolute difference to -1.0 to 1.0 compatibility scale (from its natural
        # 0.0-6.0 increasing difference scale, given each personality trait is on the scale -1 to 1)
        normalized_diff = (3.0 - diff) / 3.0
        compatibility = normalized_diff
        return compatibility

    def _init_determine_charge_increment(self):
        """Determine the increment by which the charge of this acquaintance will increase or decrease.

        The charge of an acquaintance increases as one likes the other and sees them often,
        decreases as one dislikes the other and sees them often, and regresses toward 0
        as one does not see each other (regardless of whether they like them). How much
        someone likes someone else is represented by the increment determined here, which is
        a function of their compatibility and one's extroversion and the other's agreeableness --
        following source [4], people higher in extroversion select more friends, while people high
        in agreeableness get selected more often.

        Additionally, charge intensity gets diminished (it gets brought toward 0) as a function of
        the age difference between these two people.
        """
        config = self.owner.game.config
        charge_increment = (
            self.compatibility +
            self.owner.personality.extroversion * config.owner_extroversion_boost_to_charge_multiplier +
            self.subject.personality.agreeableness * config.subject_agreeableness_boost_to_charge_multiplier
        )
        # Reduce charge intensity for sex difference
        if self.owner.male != self.subject.male:
            charge_increment *= config.charge_intensity_reduction_due_to_sex_difference
        return charge_increment

    def _init_determine_initial_spark_increment(self):
        """Determine the initial spark increment for this relationship.

        Spark captures a person's cumulative romantic attraction to another person. The
        increment has a decay rate that is specified in config.py, which means that every
        time these two people spend time together, the spark increment will decrease. For
        this reason, this method only determines the *initial* spark increment, and not the
        a spark increment that will remain static, as the charge increment does.

        A source here for how personality affects attraction is [5].

        TODO: Have this be affected by physical appearance.
        """
        config = self.owner.game.config
        # Make sure this person isn't a family member and is the sex
        # that owner is attracted to
        if self.subject in self.owner.extended_family:
            initial_spark_increment = 0
        elif self.subject.male and not self.owner.attracted_to_men:
            initial_spark_increment = 0
        elif self.subject.female and not self.owner.attracted_to_women:
            initial_spark_increment = 0
        else:
            # Affect it according to personalities using source [5]
            initial_spark_increment = 0
            initial_spark_increment += self._affect_initial_spark_increment_by_own_personality()
            initial_spark_increment += self._affect_initial_spark_increment_by_acquaintance_personality()
        return initial_spark_increment

    def _affect_initial_spark_increment_by_own_personality(self):
        """Affect the initial spark increment according to the personality of the acquaintance.

        This method relies on source [5].
        """
        config = self.owner.game.config
        sex_key = 'm' if self.owner.male else 'f'
        effect_from_own_personality = 0
        effect_from_own_personality += (
            self.subject.personality.openness_to_experience * config.openness_boost_to_spark_multiplier[sex_key]
        )
        effect_from_own_personality += (
            self.subject.personality.conscientiousness * config.conscientiousness_boost_to_spark_multiplier[sex_key]
        )
        effect_from_own_personality += (
            self.subject.personality.extroversion * config.extroversion_boost_to_spark_multiplier[sex_key]
        )
        effect_from_own_personality += (
            self.subject.personality.agreeableness * config.agreeableness_boost_to_spark_multiplier[sex_key]
        )
        effect_from_own_personality += (
            self.subject.personality.neuroticism * config.neuroticism_boost_to_spark_multiplier[sex_key]
        )
        return effect_from_own_personality

    def _affect_initial_spark_increment_by_acquaintance_personality(self):
        """Affect the initial spark increment according to the personality of the acquaintance.

        This method relies on source [5].
        """
        config = self.owner.game.config
        sex_key = 'm' if self.owner.male else 'f'
        effect_from_acquaintance_personality = 0
        effect_from_acquaintance_personality += (
            self.subject.personality.openness_to_experience * config.openness_boost_to_spark_multiplier[sex_key]
        )
        effect_from_acquaintance_personality += (
            self.subject.personality.conscientiousness * config.conscientiousness_boost_to_spark_multiplier[sex_key]
        )
        effect_from_acquaintance_personality += (
            self.subject.personality.extroversion * config.extroversion_boost_to_spark_multiplier[sex_key]
        )
        effect_from_acquaintance_personality += (
            self.subject.personality.agreeableness * config.agreeableness_boost_to_spark_multiplier[sex_key]
        )
        effect_from_acquaintance_personality += (
            self.subject.personality.neuroticism * config.neuroticism_boost_to_spark_multiplier[sex_key]
        )
        return effect_from_acquaintance_personality

    def form_or_build_up_mental_model(self):
        """Instantiate (or further fill in) a mental model of this person.

        Note: The owner of this Acquaintance may already have a mental model of the subject,
        even if they haven't met, from other people having told them about them.
        """
        observation = Observation(subject=self.subject, source=self.owner)
        if self.subject not in self.owner.mind.mental_models:
            PersonMentalModel(
                owner=self.owner, subject=self.subject, observation_or_reflection=observation
            )
        else:
            self.owner.mind.mental_models[self.subject].build_up(new_observation_or_reflection=observation)

    def progress_relationship(self):
        """Increment charge by its increment, and then potentially start a Friendship or Enmity."""
        config = self.owner.game.config
        # Progress charge, possibly leading to a Friendship or Enmity
        self.charge += self.charge_increment * self.age_difference_effect_on_charge_increment
        if self.charge > config.charge_threshold_friendship:
            Friendship(owner=self.owner, subject=self.subject, preceded_by=self)
        elif self.charge < config.charge_threshold_enmity:
            Enmity(owner=self.owner, subject=self.subject, preceded_by=self)
        # Progress spark, possibly leading to a
        self.spark_increment *= config.spark_decay_rate
        self.spark += self.spark_increment * self.age_difference_effect_on_spark_increment
        self.form_or_build_up_mental_model()

    @property
    def age_difference_effect_on_charge_increment(self):
        """Return the effect that age difference between owner and subject currently has on the charge increment."""
        config = self.owner.game.config
        charge_intensity_reduction_due_to_age_difference = (
            config.function_to_determine_how_age_difference_reduces_charge_intensity(
                age1=self.owner.age, age2=self.subject.age
            )
        )
        return charge_intensity_reduction_due_to_age_difference

    @property
    def age_difference_effect_on_spark_increment(self):
        """Return the effect that age difference between owner and subject currently has on the spark increment."""
        config = self.owner.game.config
        spark_reduction_due_to_age_difference = (
            config.function_to_determine_how_age_difference_reduces_charge_intensity(
                age1=self.owner.age, age2=self.subject.age
            )
        )
        return spark_reduction_due_to_age_difference


class Enmity(object):
    """One person's conception of their enmity with another person."""

    def __init__(self, owner, subject, preceded_by):
        """Initialize a Enmity object.

        @param owner: The person whom this conception of the enmity belongs to.
        @param subject: The other person to whom the conception pertains.
        @param preceded_by: An Acquaintance relationship that preceded this, if any.
        """
        self.type = 'enmity'
        self.owner = owner
        self.subject = subject
        self.preceded_by = preceded_by
        self.preceded_by.succeeded_by = self
        self.succeeded_by = None  # Can't be succeeded
        self.where_they_met = self.preceded_by.where_they_met
        self.when_they_met = self.preceded_by.when_they_met
        # Set this as the primary relationship owner has with subject
        self.owner.relationships[self.subject] = self
        # Inherit the charge increment and current charge of the preceding Acquaintance
        self.charge_increment = float(preceded_by.charge_increment)
        self.charge = float(preceded_by.charge)

    def progress_relationship(self):
        """Increment charge by its increment, and then potentially start a Friendship or Enmity."""
        config = self.owner.game.config
        self.charge += self.charge_increment
        if self.charge > config.charge_threshold_friendship:
            Friendship(owner=self.owner, subject=self.subject, preceded_by=self)
        elif self.charge < config.charge_threshold_enmity:
            Enmity(owner=self.owner, subject=self.subject, preceded_by=self)


class Friendship(object):
    """One person's conception of their friendship with another person."""

    def __init__(self, owner, subject, preceded_by):
        """Initialize a Friendship object.

        @param owner: The person whom this conception of the enmity belongs to.
        @param subject: The other person to whom the conception pertains.
        @param preceded_by: An Acquaintance relationship that preceded this, if any.
        """
        self.type = 'friendship'
        self.owner = owner
        self.subject = subject
        self.preceded_by = preceded_by
        self.preceded_by.succeeded_by = self
        self.succeeded_by = None  # Can't be succeeded
        self.where_they_met = self.preceded_by.where_they_met
        self.when_they_met = self.preceded_by.when_they_met
        # Set this as the primary relationship owner has with subject
        self.owner.relationships[self.subject] = self
        # Inherit the charge increment and current charge of the preceding Acquaintance
        self.charge_increment = float(preceded_by.charge_increment)
        self.charge = float(preceded_by.charge)

    def progress_relationship(self):
        """Increment charge by its increment, and then potentially start a Friendship or Enmity."""
        config = self.owner.game.config
        self.charge += self.charge_increment
        if self.charge > config.charge_threshold_friendship:
            Friendship(owner=self.owner, subject=self.subject, preceded_by=self)
        elif self.charge < config.charge_threshold_enmity:
            Enmity(owner=self.owner, subject=self.subject, preceded_by=self)


class Kinship(object):
    """One person's conception of their family relationship with another person."""

    def __init__(self, owner, subject, relationship):
        """Initialize a Kinship object.

        @param owner: The person whom this conception of the enmity belongs to.
        @param subject: The other person to whom the conception pertains.
        @param relationship: A string representing the specific family relationship.
        """
        self.type = 'kinship'
        self.owner = owner
        self.subject = subject
        self.relationship = relationship
        self.succeeded_by = None  # May get set by a succeeding Acquaintance object
        self.where_they_met = None  # When they meet, an Acquaintance object is instantiated
        self.when_they_met = None
        # Set this as the primary relationship owner has with subject
        self.owner.relationships[self.subject] = self