"""
Culture preferences for all 16 ideologies.

Each ideology has an opinion about every culture option across all 8 categories,
3 levels, and 2 options per level (48 entries total per ideology).

Preference labels:
  must-have   — goal option or strongly preferred prerequisite on their goal path
  preferred   — aligns with worldview, would buy if affordable
  indifferent — no strong opinion
  antithesis  — opposes ideology, would block if possible
"""

from mechanics.cultures import CULTURE_TREE

VALID_LABELS = {"must-have", "preferred", "indifferent", "antithesis"}

# ---------------------------------------------------------------------------
# Master preference table — 16 ideologies × 8 categories × 3 levels × 2 opts
# ---------------------------------------------------------------------------

CULTURE_PREFERENCES: dict = {

    # ── Progressionist ────────────────────────────────────────────────────
    # Primary: Democracy (politics L3)
    # Secondary1: Emotional (mindset L2)
    # Secondary2: Air (natural_affinity L2)
    # Tertiary: production
    "Progressionist": {
        "politics": {
            1: {"Anarchy": "must-have", "Authoritarian": "antithesis"},
            2: {"Monarchy": "antithesis", "Republic": "must-have"},
            3: {"Democracy": "must-have", "Empire": "antithesis"},
        },
        "property": {
            1: {"Personal": "preferred", "Communal": "indifferent"},
            2: {"Barter": "indifferent", "Currency": "preferred"},
            3: {"Banking": "indifferent", "Taxes": "indifferent"},
        },
        "spirituality": {
            1: {"Ancestors": "indifferent", "Nature": "preferred"},
            2: {"Monotheism": "indifferent", "Polytheism": "preferred"},
            3: {"Science": "preferred", "Mysticism": "indifferent"},
        },
        "mindset": {
            1: {"Impulsive": "must-have", "Cautious": "antithesis"},
            2: {"Rational": "antithesis", "Emotional": "must-have"},
            3: {"Diplomatic": "preferred", "Isolationist": "indifferent"},
        },
        "social_order": {
            1: {"Fraternal": "preferred", "Familial": "indifferent"},
            2: {"Tribal": "indifferent", "Hierarchical": "antithesis"},
            3: {"Class": "antithesis", "Meritocracy": "preferred"},
        },
        "values": {
            1: {"Strength": "indifferent", "Knowledge": "preferred"},
            2: {"Talent": "preferred", "Skill": "indifferent"},
            3: {"Prestige": "preferred", "Power": "antithesis"},
        },
        "production": {
            1: {"Farming": "preferred", "Hunting": "indifferent"},
            2: {"Raiding": "indifferent", "Trading": "preferred"},
            3: {"Manufacturing": "preferred", "Mining": "indifferent"},
        },
        "natural_affinity": {
            1: {"Earth": "indifferent", "Water": "must-have"},
            2: {"Air": "must-have", "Fire": "antithesis"},
            3: {"Light": "preferred", "Dark": "indifferent"},
        },
    },

    # ── Conqueror ─────────────────────────────────────────────────────────
    # Primary: Empire (politics L3)
    # Secondary1: Tribal (social_order L2)
    # Secondary2: Raiding (production L2)
    # Tertiary: values
    "Conqueror": {
        "politics": {
            1: {"Anarchy": "antithesis", "Authoritarian": "must-have"},
            2: {"Monarchy": "must-have", "Republic": "antithesis"},
            3: {"Democracy": "antithesis", "Empire": "must-have"},
        },
        "property": {
            1: {"Personal": "indifferent", "Communal": "preferred"},
            2: {"Barter": "indifferent", "Currency": "preferred"},
            3: {"Banking": "indifferent", "Taxes": "preferred"},
        },
        "spirituality": {
            1: {"Ancestors": "preferred", "Nature": "indifferent"},
            2: {"Monotheism": "preferred", "Polytheism": "indifferent"},
            3: {"Science": "indifferent", "Mysticism": "indifferent"},
        },
        "mindset": {
            1: {"Impulsive": "preferred", "Cautious": "indifferent"},
            2: {"Rational": "indifferent", "Emotional": "preferred"},
            3: {"Diplomatic": "antithesis", "Isolationist": "preferred"},
        },
        "social_order": {
            1: {"Fraternal": "must-have", "Familial": "antithesis"},
            2: {"Tribal": "must-have", "Hierarchical": "antithesis"},
            3: {"Class": "indifferent", "Meritocracy": "preferred"},
        },
        "values": {
            1: {"Strength": "preferred", "Knowledge": "indifferent"},
            2: {"Talent": "indifferent", "Skill": "preferred"},
            3: {"Prestige": "indifferent", "Power": "preferred"},
        },
        "production": {
            1: {"Farming": "antithesis", "Hunting": "must-have"},
            2: {"Raiding": "must-have", "Trading": "antithesis"},
            3: {"Manufacturing": "indifferent", "Mining": "preferred"},
        },
        "natural_affinity": {
            1: {"Earth": "preferred", "Water": "indifferent"},
            2: {"Air": "indifferent", "Fire": "preferred"},
            3: {"Light": "indifferent", "Dark": "preferred"},
        },
    },

    # ── Investor ──────────────────────────────────────────────────────────
    # Primary: Banking (property L3)
    # Secondary1: Rational (mindset L2)
    # Secondary2: Trading (production L2)
    # Tertiary: social_order
    "Investor": {
        "politics": {
            1: {"Anarchy": "antithesis", "Authoritarian": "indifferent"},
            2: {"Monarchy": "indifferent", "Republic": "preferred"},
            3: {"Democracy": "preferred", "Empire": "indifferent"},
        },
        "property": {
            1: {"Personal": "must-have", "Communal": "antithesis"},
            2: {"Barter": "antithesis", "Currency": "must-have"},
            3: {"Banking": "must-have", "Taxes": "antithesis"},
        },
        "spirituality": {
            1: {"Ancestors": "indifferent", "Nature": "indifferent"},
            2: {"Monotheism": "indifferent", "Polytheism": "indifferent"},
            3: {"Science": "preferred", "Mysticism": "indifferent"},
        },
        "mindset": {
            1: {"Impulsive": "antithesis", "Cautious": "must-have"},
            2: {"Rational": "must-have", "Emotional": "antithesis"},
            3: {"Diplomatic": "preferred", "Isolationist": "indifferent"},
        },
        "social_order": {
            1: {"Fraternal": "indifferent", "Familial": "preferred"},
            2: {"Tribal": "indifferent", "Hierarchical": "preferred"},
            3: {"Class": "preferred", "Meritocracy": "indifferent"},
        },
        "values": {
            1: {"Strength": "indifferent", "Knowledge": "preferred"},
            2: {"Talent": "preferred", "Skill": "indifferent"},
            3: {"Prestige": "preferred", "Power": "indifferent"},
        },
        "production": {
            1: {"Farming": "must-have", "Hunting": "antithesis"},
            2: {"Raiding": "antithesis", "Trading": "must-have"},
            3: {"Manufacturing": "preferred", "Mining": "indifferent"},
        },
        "natural_affinity": {
            1: {"Earth": "preferred", "Water": "indifferent"},
            2: {"Air": "indifferent", "Fire": "indifferent"},
            3: {"Light": "preferred", "Dark": "antithesis"},
        },
    },

    # ── Tyrant ────────────────────────────────────────────────────────────
    # Primary: Taxes (property L3)
    # Secondary1: Monotheism (spirituality L2)
    # Secondary2: Fire (natural_affinity L2)
    # Tertiary: mindset
    "Tyrant": {
        "politics": {
            1: {"Anarchy": "antithesis", "Authoritarian": "preferred"},
            2: {"Monarchy": "preferred", "Republic": "antithesis"},
            3: {"Democracy": "antithesis", "Empire": "preferred"},
        },
        "property": {
            1: {"Personal": "antithesis", "Communal": "must-have"},
            2: {"Barter": "antithesis", "Currency": "must-have"},
            3: {"Banking": "antithesis", "Taxes": "must-have"},
        },
        "spirituality": {
            1: {"Ancestors": "must-have", "Nature": "antithesis"},
            2: {"Monotheism": "must-have", "Polytheism": "antithesis"},
            3: {"Science": "indifferent", "Mysticism": "preferred"},
        },
        "mindset": {
            1: {"Impulsive": "indifferent", "Cautious": "preferred"},
            2: {"Rational": "preferred", "Emotional": "indifferent"},
            3: {"Diplomatic": "indifferent", "Isolationist": "preferred"},
        },
        "social_order": {
            1: {"Fraternal": "indifferent", "Familial": "preferred"},
            2: {"Tribal": "antithesis", "Hierarchical": "preferred"},
            3: {"Class": "preferred", "Meritocracy": "antithesis"},
        },
        "values": {
            1: {"Strength": "preferred", "Knowledge": "indifferent"},
            2: {"Talent": "indifferent", "Skill": "indifferent"},
            3: {"Prestige": "indifferent", "Power": "preferred"},
        },
        "production": {
            1: {"Farming": "preferred", "Hunting": "indifferent"},
            2: {"Raiding": "indifferent", "Trading": "preferred"},
            3: {"Manufacturing": "indifferent", "Mining": "preferred"},
        },
        "natural_affinity": {
            1: {"Earth": "must-have", "Water": "antithesis"},
            2: {"Air": "antithesis", "Fire": "must-have"},
            3: {"Light": "indifferent", "Dark": "preferred"},
        },
    },

    # ── Empiricist ────────────────────────────────────────────────────────
    # Primary: Science (spirituality L3)
    # Secondary1: Rational (mindset L2)
    # Secondary2: Skill (values L2)
    # Tertiary: natural_affinity
    "Empiricist": {
        "politics": {
            1: {"Anarchy": "indifferent", "Authoritarian": "indifferent"},
            2: {"Monarchy": "indifferent", "Republic": "preferred"},
            3: {"Democracy": "preferred", "Empire": "indifferent"},
        },
        "property": {
            1: {"Personal": "preferred", "Communal": "indifferent"},
            2: {"Barter": "antithesis", "Currency": "preferred"},
            3: {"Banking": "preferred", "Taxes": "indifferent"},
        },
        "spirituality": {
            1: {"Ancestors": "must-have", "Nature": "antithesis"},
            2: {"Monotheism": "antithesis", "Polytheism": "must-have"},
            3: {"Science": "must-have", "Mysticism": "antithesis"},
        },
        "mindset": {
            1: {"Impulsive": "antithesis", "Cautious": "must-have"},
            2: {"Rational": "must-have", "Emotional": "antithesis"},
            3: {"Diplomatic": "preferred", "Isolationist": "indifferent"},
        },
        "social_order": {
            1: {"Fraternal": "preferred", "Familial": "indifferent"},
            2: {"Tribal": "indifferent", "Hierarchical": "indifferent"},
            3: {"Class": "antithesis", "Meritocracy": "preferred"},
        },
        "values": {
            1: {"Strength": "antithesis", "Knowledge": "must-have"},
            2: {"Talent": "antithesis", "Skill": "must-have"},
            3: {"Prestige": "indifferent", "Power": "indifferent"},
        },
        "production": {
            1: {"Farming": "preferred", "Hunting": "indifferent"},
            2: {"Raiding": "antithesis", "Trading": "preferred"},
            3: {"Manufacturing": "preferred", "Mining": "indifferent"},
        },
        "natural_affinity": {
            1: {"Earth": "preferred", "Water": "indifferent"},
            2: {"Air": "preferred", "Fire": "indifferent"},
            3: {"Light": "preferred", "Dark": "indifferent"},
        },
    },

    # ── Mystic ────────────────────────────────────────────────────────────
    # Primary: Mysticism (spirituality L3)
    # Secondary1: Emotional (mindset L2)
    # Secondary2: Air (natural_affinity L2)
    # Tertiary: values
    "Mystic": {
        "politics": {
            1: {"Anarchy": "preferred", "Authoritarian": "indifferent"},
            2: {"Monarchy": "indifferent", "Republic": "indifferent"},
            3: {"Democracy": "indifferent", "Empire": "indifferent"},
        },
        "property": {
            1: {"Personal": "indifferent", "Communal": "preferred"},
            2: {"Barter": "preferred", "Currency": "indifferent"},
            3: {"Banking": "antithesis", "Taxes": "indifferent"},
        },
        "spirituality": {
            1: {"Ancestors": "antithesis", "Nature": "must-have"},
            2: {"Monotheism": "antithesis", "Polytheism": "must-have"},
            3: {"Science": "antithesis", "Mysticism": "must-have"},
        },
        "mindset": {
            1: {"Impulsive": "must-have", "Cautious": "antithesis"},
            2: {"Rational": "antithesis", "Emotional": "must-have"},
            3: {"Diplomatic": "indifferent", "Isolationist": "preferred"},
        },
        "social_order": {
            1: {"Fraternal": "preferred", "Familial": "indifferent"},
            2: {"Tribal": "preferred", "Hierarchical": "antithesis"},
            3: {"Class": "antithesis", "Meritocracy": "indifferent"},
        },
        "values": {
            1: {"Strength": "indifferent", "Knowledge": "preferred"},
            2: {"Talent": "preferred", "Skill": "indifferent"},
            3: {"Prestige": "preferred", "Power": "indifferent"},
        },
        "production": {
            1: {"Farming": "preferred", "Hunting": "indifferent"},
            2: {"Raiding": "antithesis", "Trading": "indifferent"},
            3: {"Manufacturing": "indifferent", "Mining": "indifferent"},
        },
        "natural_affinity": {
            1: {"Earth": "antithesis", "Water": "must-have"},
            2: {"Air": "must-have", "Fire": "antithesis"},
            3: {"Light": "preferred", "Dark": "indifferent"},
        },
    },

    # ── Influencer ────────────────────────────────────────────────────────
    # Primary: Diplomatic (mindset L3)
    # Secondary1: Talent (values L2)
    # Secondary2: Trading (production L2)
    # Tertiary: politics
    "Influencer": {
        "politics": {
            1: {"Anarchy": "indifferent", "Authoritarian": "indifferent"},
            2: {"Monarchy": "indifferent", "Republic": "preferred"},
            3: {"Democracy": "preferred", "Empire": "indifferent"},
        },
        "property": {
            1: {"Personal": "preferred", "Communal": "indifferent"},
            2: {"Barter": "indifferent", "Currency": "preferred"},
            3: {"Banking": "preferred", "Taxes": "indifferent"},
        },
        "spirituality": {
            1: {"Ancestors": "indifferent", "Nature": "indifferent"},
            2: {"Monotheism": "indifferent", "Polytheism": "preferred"},
            3: {"Science": "indifferent", "Mysticism": "indifferent"},
        },
        "mindset": {
            1: {"Impulsive": "antithesis", "Cautious": "must-have"},
            2: {"Rational": "must-have", "Emotional": "antithesis"},
            3: {"Diplomatic": "must-have", "Isolationist": "antithesis"},
        },
        "social_order": {
            1: {"Fraternal": "preferred", "Familial": "indifferent"},
            2: {"Tribal": "preferred", "Hierarchical": "indifferent"},
            3: {"Class": "indifferent", "Meritocracy": "preferred"},
        },
        "values": {
            1: {"Strength": "antithesis", "Knowledge": "must-have"},
            2: {"Talent": "must-have", "Skill": "antithesis"},
            3: {"Prestige": "preferred", "Power": "indifferent"},
        },
        "production": {
            1: {"Farming": "must-have", "Hunting": "antithesis"},
            2: {"Raiding": "antithesis", "Trading": "must-have"},
            3: {"Manufacturing": "indifferent", "Mining": "indifferent"},
        },
        "natural_affinity": {
            1: {"Earth": "indifferent", "Water": "preferred"},
            2: {"Air": "preferred", "Fire": "indifferent"},
            3: {"Light": "preferred", "Dark": "antithesis"},
        },
    },

    # ── Survivalist ───────────────────────────────────────────────────────
    # Primary: Isolationist (mindset L3)
    # Secondary1: Monotheism (spirituality L2)
    # Secondary2: Monarchy (politics L2)
    # Tertiary: production
    "Survivalist": {
        "politics": {
            1: {"Anarchy": "antithesis", "Authoritarian": "must-have"},
            2: {"Monarchy": "must-have", "Republic": "antithesis"},
            3: {"Democracy": "indifferent", "Empire": "preferred"},
        },
        "property": {
            1: {"Personal": "preferred", "Communal": "indifferent"},
            2: {"Barter": "preferred", "Currency": "indifferent"},
            3: {"Banking": "indifferent", "Taxes": "indifferent"},
        },
        "spirituality": {
            1: {"Ancestors": "must-have", "Nature": "antithesis"},
            2: {"Monotheism": "must-have", "Polytheism": "antithesis"},
            3: {"Science": "indifferent", "Mysticism": "preferred"},
        },
        "mindset": {
            1: {"Impulsive": "antithesis", "Cautious": "must-have"},
            2: {"Rational": "must-have", "Emotional": "antithesis"},
            3: {"Diplomatic": "antithesis", "Isolationist": "must-have"},
        },
        "social_order": {
            1: {"Fraternal": "indifferent", "Familial": "preferred"},
            2: {"Tribal": "preferred", "Hierarchical": "indifferent"},
            3: {"Class": "indifferent", "Meritocracy": "indifferent"},
        },
        "values": {
            1: {"Strength": "preferred", "Knowledge": "indifferent"},
            2: {"Talent": "indifferent", "Skill": "preferred"},
            3: {"Prestige": "indifferent", "Power": "indifferent"},
        },
        "production": {
            1: {"Farming": "preferred", "Hunting": "indifferent"},
            2: {"Raiding": "indifferent", "Trading": "indifferent"},
            3: {"Manufacturing": "indifferent", "Mining": "preferred"},
        },
        "natural_affinity": {
            1: {"Earth": "preferred", "Water": "indifferent"},
            2: {"Air": "indifferent", "Fire": "indifferent"},
            3: {"Light": "indifferent", "Dark": "indifferent"},
        },
    },

    # ── Noble ─────────────────────────────────────────────────────────────
    # Primary: Class (social_order L3)
    # Secondary1: Republic (politics L2)
    # Secondary2: Talent (values L2)
    # Tertiary: spirituality
    "Noble": {
        "politics": {
            1: {"Anarchy": "antithesis", "Authoritarian": "must-have"},
            2: {"Monarchy": "antithesis", "Republic": "must-have"},
            3: {"Democracy": "preferred", "Empire": "indifferent"},
        },
        "property": {
            1: {"Personal": "preferred", "Communal": "antithesis"},
            2: {"Barter": "indifferent", "Currency": "preferred"},
            3: {"Banking": "preferred", "Taxes": "indifferent"},
        },
        "spirituality": {
            1: {"Ancestors": "preferred", "Nature": "indifferent"},
            2: {"Monotheism": "preferred", "Polytheism": "indifferent"},
            3: {"Science": "indifferent", "Mysticism": "preferred"},
        },
        "mindset": {
            1: {"Impulsive": "indifferent", "Cautious": "preferred"},
            2: {"Rational": "preferred", "Emotional": "indifferent"},
            3: {"Diplomatic": "preferred", "Isolationist": "antithesis"},
        },
        "social_order": {
            1: {"Fraternal": "antithesis", "Familial": "must-have"},
            2: {"Tribal": "antithesis", "Hierarchical": "must-have"},
            3: {"Class": "must-have", "Meritocracy": "antithesis"},
        },
        "values": {
            1: {"Strength": "indifferent", "Knowledge": "must-have"},
            2: {"Talent": "must-have", "Skill": "antithesis"},
            3: {"Prestige": "preferred", "Power": "indifferent"},
        },
        "production": {
            1: {"Farming": "preferred", "Hunting": "indifferent"},
            2: {"Raiding": "antithesis", "Trading": "preferred"},
            3: {"Manufacturing": "indifferent", "Mining": "indifferent"},
        },
        "natural_affinity": {
            1: {"Earth": "indifferent", "Water": "indifferent"},
            2: {"Air": "preferred", "Fire": "indifferent"},
            3: {"Light": "preferred", "Dark": "antithesis"},
        },
    },

    # ── Champion ──────────────────────────────────────────────────────────
    # Primary: Meritocracy (social_order L3)
    # Secondary1: Currency (property L2)
    # Secondary2: Raiding (production L2)
    # Tertiary: mindset
    "Champion": {
        "politics": {
            1: {"Anarchy": "preferred", "Authoritarian": "indifferent"},
            2: {"Monarchy": "antithesis", "Republic": "preferred"},
            3: {"Democracy": "preferred", "Empire": "antithesis"},
        },
        "property": {
            1: {"Personal": "must-have", "Communal": "antithesis"},
            2: {"Barter": "antithesis", "Currency": "must-have"},
            3: {"Banking": "indifferent", "Taxes": "indifferent"},
        },
        "spirituality": {
            1: {"Ancestors": "indifferent", "Nature": "indifferent"},
            2: {"Monotheism": "indifferent", "Polytheism": "indifferent"},
            3: {"Science": "preferred", "Mysticism": "indifferent"},
        },
        "mindset": {
            1: {"Impulsive": "preferred", "Cautious": "indifferent"},
            2: {"Rational": "preferred", "Emotional": "indifferent"},
            3: {"Diplomatic": "indifferent", "Isolationist": "preferred"},
        },
        "social_order": {
            1: {"Fraternal": "must-have", "Familial": "antithesis"},
            2: {"Tribal": "must-have", "Hierarchical": "antithesis"},
            3: {"Class": "antithesis", "Meritocracy": "must-have"},
        },
        "values": {
            1: {"Strength": "preferred", "Knowledge": "indifferent"},
            2: {"Talent": "indifferent", "Skill": "preferred"},
            3: {"Prestige": "indifferent", "Power": "preferred"},
        },
        "production": {
            1: {"Farming": "antithesis", "Hunting": "must-have"},
            2: {"Raiding": "must-have", "Trading": "antithesis"},
            3: {"Manufacturing": "indifferent", "Mining": "preferred"},
        },
        "natural_affinity": {
            1: {"Earth": "preferred", "Water": "indifferent"},
            2: {"Air": "indifferent", "Fire": "preferred"},
            3: {"Light": "indifferent", "Dark": "indifferent"},
        },
    },

    # ── Competitor ─────────────────────────────────────────────────────────
    # Primary: Prestige (values L3)
    # Secondary1: Barter (property L2)
    # Secondary2: Hierarchical (social_order L2)
    # Tertiary: natural_affinity
    "Competitor": {
        "politics": {
            1: {"Anarchy": "indifferent", "Authoritarian": "preferred"},
            2: {"Monarchy": "indifferent", "Republic": "indifferent"},
            3: {"Democracy": "indifferent", "Empire": "preferred"},
        },
        "property": {
            1: {"Personal": "must-have", "Communal": "antithesis"},
            2: {"Barter": "must-have", "Currency": "antithesis"},
            3: {"Banking": "indifferent", "Taxes": "indifferent"},
        },
        "spirituality": {
            1: {"Ancestors": "indifferent", "Nature": "indifferent"},
            2: {"Monotheism": "indifferent", "Polytheism": "indifferent"},
            3: {"Science": "indifferent", "Mysticism": "indifferent"},
        },
        "mindset": {
            1: {"Impulsive": "preferred", "Cautious": "indifferent"},
            2: {"Rational": "preferred", "Emotional": "indifferent"},
            3: {"Diplomatic": "indifferent", "Isolationist": "preferred"},
        },
        "social_order": {
            1: {"Fraternal": "antithesis", "Familial": "must-have"},
            2: {"Tribal": "antithesis", "Hierarchical": "must-have"},
            3: {"Class": "preferred", "Meritocracy": "indifferent"},
        },
        "values": {
            1: {"Strength": "must-have", "Knowledge": "antithesis"},
            2: {"Talent": "must-have", "Skill": "antithesis"},
            3: {"Prestige": "must-have", "Power": "antithesis"},
        },
        "production": {
            1: {"Farming": "indifferent", "Hunting": "preferred"},
            2: {"Raiding": "preferred", "Trading": "indifferent"},
            3: {"Manufacturing": "indifferent", "Mining": "indifferent"},
        },
        "natural_affinity": {
            1: {"Earth": "indifferent", "Water": "preferred"},
            2: {"Air": "preferred", "Fire": "indifferent"},
            3: {"Light": "preferred", "Dark": "indifferent"},
        },
    },

    # ── Warlord ───────────────────────────────────────────────────────────
    # Primary: Power (values L3)
    # Secondary1: Monarchy (politics L2)
    # Secondary2: Polytheism (spirituality L2)
    # Tertiary: property
    "Warlord": {
        "politics": {
            1: {"Anarchy": "antithesis", "Authoritarian": "must-have"},
            2: {"Monarchy": "must-have", "Republic": "antithesis"},
            3: {"Democracy": "antithesis", "Empire": "preferred"},
        },
        "property": {
            1: {"Personal": "indifferent", "Communal": "preferred"},
            2: {"Barter": "indifferent", "Currency": "preferred"},
            3: {"Banking": "indifferent", "Taxes": "preferred"},
        },
        "spirituality": {
            1: {"Ancestors": "antithesis", "Nature": "must-have"},
            2: {"Monotheism": "antithesis", "Polytheism": "must-have"},
            3: {"Science": "indifferent", "Mysticism": "preferred"},
        },
        "mindset": {
            1: {"Impulsive": "preferred", "Cautious": "indifferent"},
            2: {"Rational": "indifferent", "Emotional": "preferred"},
            3: {"Diplomatic": "antithesis", "Isolationist": "preferred"},
        },
        "social_order": {
            1: {"Fraternal": "indifferent", "Familial": "preferred"},
            2: {"Tribal": "preferred", "Hierarchical": "indifferent"},
            3: {"Class": "indifferent", "Meritocracy": "indifferent"},
        },
        "values": {
            1: {"Strength": "must-have", "Knowledge": "antithesis"},
            2: {"Talent": "antithesis", "Skill": "must-have"},
            3: {"Prestige": "antithesis", "Power": "must-have"},
        },
        "production": {
            1: {"Farming": "indifferent", "Hunting": "preferred"},
            2: {"Raiding": "preferred", "Trading": "indifferent"},
            3: {"Manufacturing": "indifferent", "Mining": "preferred"},
        },
        "natural_affinity": {
            1: {"Earth": "preferred", "Water": "indifferent"},
            2: {"Air": "indifferent", "Fire": "preferred"},
            3: {"Light": "indifferent", "Dark": "preferred"},
        },
    },

    # ── Industrialist ─────────────────────────────────────────────────────
    # Primary: Manufacturing (production L3)
    # Secondary1: Fire (natural_affinity L2)
    # Secondary2: Skill (values L2)
    # Tertiary: property
    "Industrialist": {
        "politics": {
            1: {"Anarchy": "indifferent", "Authoritarian": "preferred"},
            2: {"Monarchy": "indifferent", "Republic": "preferred"},
            3: {"Democracy": "indifferent", "Empire": "preferred"},
        },
        "property": {
            1: {"Personal": "preferred", "Communal": "indifferent"},
            2: {"Barter": "indifferent", "Currency": "preferred"},
            3: {"Banking": "preferred", "Taxes": "indifferent"},
        },
        "spirituality": {
            1: {"Ancestors": "indifferent", "Nature": "indifferent"},
            2: {"Monotheism": "indifferent", "Polytheism": "indifferent"},
            3: {"Science": "preferred", "Mysticism": "antithesis"},
        },
        "mindset": {
            1: {"Impulsive": "indifferent", "Cautious": "preferred"},
            2: {"Rational": "preferred", "Emotional": "indifferent"},
            3: {"Diplomatic": "indifferent", "Isolationist": "indifferent"},
        },
        "social_order": {
            1: {"Fraternal": "indifferent", "Familial": "indifferent"},
            2: {"Tribal": "indifferent", "Hierarchical": "preferred"},
            3: {"Class": "preferred", "Meritocracy": "indifferent"},
        },
        "values": {
            1: {"Strength": "must-have", "Knowledge": "antithesis"},
            2: {"Talent": "antithesis", "Skill": "must-have"},
            3: {"Prestige": "indifferent", "Power": "preferred"},
        },
        "production": {
            1: {"Farming": "must-have", "Hunting": "antithesis"},
            2: {"Raiding": "antithesis", "Trading": "must-have"},
            3: {"Manufacturing": "must-have", "Mining": "antithesis"},
        },
        "natural_affinity": {
            1: {"Earth": "must-have", "Water": "antithesis"},
            2: {"Air": "antithesis", "Fire": "must-have"},
            3: {"Light": "indifferent", "Dark": "indifferent"},
        },
    },

    # ── Exploitationist ──────────────────────────────────────────────────
    # Primary: Mining (production L3)
    # Secondary1: Barter (property L2)
    # Secondary2: Hierarchical (social_order L2)
    # Tertiary: natural_affinity
    "Exploitationist": {
        "politics": {
            1: {"Anarchy": "preferred", "Authoritarian": "indifferent"},
            2: {"Monarchy": "indifferent", "Republic": "indifferent"},
            3: {"Democracy": "indifferent", "Empire": "preferred"},
        },
        "property": {
            1: {"Personal": "must-have", "Communal": "antithesis"},
            2: {"Barter": "must-have", "Currency": "antithesis"},
            3: {"Banking": "indifferent", "Taxes": "indifferent"},
        },
        "spirituality": {
            1: {"Ancestors": "indifferent", "Nature": "preferred"},
            2: {"Monotheism": "indifferent", "Polytheism": "indifferent"},
            3: {"Science": "preferred", "Mysticism": "indifferent"},
        },
        "mindset": {
            1: {"Impulsive": "preferred", "Cautious": "indifferent"},
            2: {"Rational": "preferred", "Emotional": "indifferent"},
            3: {"Diplomatic": "indifferent", "Isolationist": "preferred"},
        },
        "social_order": {
            1: {"Fraternal": "antithesis", "Familial": "must-have"},
            2: {"Tribal": "antithesis", "Hierarchical": "must-have"},
            3: {"Class": "preferred", "Meritocracy": "indifferent"},
        },
        "values": {
            1: {"Strength": "preferred", "Knowledge": "indifferent"},
            2: {"Talent": "indifferent", "Skill": "preferred"},
            3: {"Prestige": "indifferent", "Power": "preferred"},
        },
        "production": {
            1: {"Farming": "antithesis", "Hunting": "must-have"},
            2: {"Raiding": "must-have", "Trading": "antithesis"},
            3: {"Manufacturing": "antithesis", "Mining": "must-have"},
        },
        "natural_affinity": {
            1: {"Earth": "preferred", "Water": "indifferent"},
            2: {"Air": "indifferent", "Fire": "preferred"},
            3: {"Light": "indifferent", "Dark": "preferred"},
        },
    },

    # ── Illuminator ───────────────────────────────────────────────────────
    # Primary: Light (natural_affinity L3)
    # Secondary1: Republic (politics L2)
    # Secondary2: Tribal (social_order L2)
    # Tertiary: spirituality
    "Illuminator": {
        "politics": {
            1: {"Anarchy": "must-have", "Authoritarian": "antithesis"},
            2: {"Monarchy": "antithesis", "Republic": "must-have"},
            3: {"Democracy": "preferred", "Empire": "indifferent"},
        },
        "property": {
            1: {"Personal": "indifferent", "Communal": "preferred"},
            2: {"Barter": "indifferent", "Currency": "indifferent"},
            3: {"Banking": "indifferent", "Taxes": "indifferent"},
        },
        "spirituality": {
            1: {"Ancestors": "indifferent", "Nature": "preferred"},
            2: {"Monotheism": "preferred", "Polytheism": "indifferent"},
            3: {"Science": "preferred", "Mysticism": "indifferent"},
        },
        "mindset": {
            1: {"Impulsive": "indifferent", "Cautious": "preferred"},
            2: {"Rational": "preferred", "Emotional": "indifferent"},
            3: {"Diplomatic": "preferred", "Isolationist": "antithesis"},
        },
        "social_order": {
            1: {"Fraternal": "must-have", "Familial": "antithesis"},
            2: {"Tribal": "must-have", "Hierarchical": "antithesis"},
            3: {"Class": "indifferent", "Meritocracy": "preferred"},
        },
        "values": {
            1: {"Strength": "indifferent", "Knowledge": "preferred"},
            2: {"Talent": "preferred", "Skill": "indifferent"},
            3: {"Prestige": "preferred", "Power": "antithesis"},
        },
        "production": {
            1: {"Farming": "preferred", "Hunting": "indifferent"},
            2: {"Raiding": "antithesis", "Trading": "preferred"},
            3: {"Manufacturing": "indifferent", "Mining": "indifferent"},
        },
        "natural_affinity": {
            1: {"Earth": "must-have", "Water": "antithesis"},
            2: {"Air": "must-have", "Fire": "antithesis"},
            3: {"Light": "must-have", "Dark": "antithesis"},
        },
    },

    # ── Deceiver ──────────────────────────────────────────────────────────
    # Primary: Dark (natural_affinity L3)
    # Secondary1: Currency (property L2)
    # Secondary2: Polytheism (spirituality L2)
    # Tertiary: politics
    "Deceiver": {
        "politics": {
            1: {"Anarchy": "preferred", "Authoritarian": "indifferent"},
            2: {"Monarchy": "indifferent", "Republic": "indifferent"},
            3: {"Democracy": "indifferent", "Empire": "preferred"},
        },
        "property": {
            1: {"Personal": "must-have", "Communal": "antithesis"},
            2: {"Barter": "antithesis", "Currency": "must-have"},
            3: {"Banking": "indifferent", "Taxes": "indifferent"},
        },
        "spirituality": {
            1: {"Ancestors": "antithesis", "Nature": "must-have"},
            2: {"Monotheism": "antithesis", "Polytheism": "must-have"},
            3: {"Science": "indifferent", "Mysticism": "preferred"},
        },
        "mindset": {
            1: {"Impulsive": "preferred", "Cautious": "indifferent"},
            2: {"Rational": "indifferent", "Emotional": "preferred"},
            3: {"Diplomatic": "preferred", "Isolationist": "indifferent"},
        },
        "social_order": {
            1: {"Fraternal": "indifferent", "Familial": "preferred"},
            2: {"Tribal": "indifferent", "Hierarchical": "preferred"},
            3: {"Class": "preferred", "Meritocracy": "indifferent"},
        },
        "values": {
            1: {"Strength": "indifferent", "Knowledge": "preferred"},
            2: {"Talent": "preferred", "Skill": "indifferent"},
            3: {"Prestige": "preferred", "Power": "indifferent"},
        },
        "production": {
            1: {"Farming": "indifferent", "Hunting": "preferred"},
            2: {"Raiding": "preferred", "Trading": "indifferent"},
            3: {"Manufacturing": "indifferent", "Mining": "indifferent"},
        },
        "natural_affinity": {
            1: {"Earth": "antithesis", "Water": "must-have"},
            2: {"Air": "antithesis", "Fire": "must-have"},
            3: {"Light": "antithesis", "Dark": "must-have"},
        },
    },
}


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_culture_preferences(ideology_names: list[str]) -> None:
    """Validate that CULTURE_PREFERENCES covers every ideology and option correctly.

    Raises ValueError on any mismatch.
    """
    for name in ideology_names:
        if name not in CULTURE_PREFERENCES:
            raise ValueError(
                f"Ideology {name!r} missing from CULTURE_PREFERENCES"
            )

        prefs = CULTURE_PREFERENCES[name]

        for cat_key, cat_data in CULTURE_TREE.items():
            if cat_key not in prefs:
                raise ValueError(
                    f"Ideology {name!r}: missing category {cat_key!r}"
                )

            for level in (1, 2, 3):
                if level not in prefs[cat_key]:
                    raise ValueError(
                        f"Ideology {name!r}, category {cat_key!r}: "
                        f"missing level {level}"
                    )

                expected_options = cat_data["levels"][level]["options"]
                level_prefs = prefs[cat_key][level]

                for opt in expected_options:
                    if opt not in level_prefs:
                        raise ValueError(
                            f"Ideology {name!r}, {cat_key!r} L{level}: "
                            f"missing option {opt!r}"
                        )

                for opt in level_prefs:
                    if opt not in expected_options:
                        raise ValueError(
                            f"Ideology {name!r}, {cat_key!r} L{level}: "
                            f"unexpected option {opt!r}"
                        )

                for opt, label in level_prefs.items():
                    if label not in VALID_LABELS:
                        raise ValueError(
                            f"Ideology {name!r}, {cat_key!r} L{level} "
                            f"{opt!r}: invalid label {label!r}"
                        )


# ---------------------------------------------------------------------------
# Merge helper
# ---------------------------------------------------------------------------

def merge_preferences(ideologies_dict: dict) -> None:
    """Attach culture_preferences to each ideology in *ideologies_dict*.

    Validates first, then mutates each ideology entry in place.
    """
    validate_culture_preferences(list(ideologies_dict.keys()))

    for name in ideologies_dict:
        ideologies_dict[name]["culture_preferences"] = CULTURE_PREFERENCES[name]
