"""
All 16 settler ideologies with full psychological and narrative depth.

Each entry includes:
  description         – one-line summary
  worldview           – fundamental belief about power and society
  primary             – {category, level, option, motivation, enemy_option, enemy_reason}
  secondary           – list of 2x {category, level, option, motivation, enemy_option, enemy_reason}
  tertiary            – {category, motivation}
  core_fear           – drives irrational / self-sacrificing behavior
  blind_spot          – what they consistently misread
  cooperation_currency – what you must offer to get genuine cooperation
  betrayal_pattern    – how and when they defect
  voice               – tone and register for LLM narrative output
"""

IDEOLOGIES: dict = {

    "Progressionist": {
        "description": "Champions innovation, social progress, and transformative change.",
        "worldview": (
            "Power belongs to those who can articulate a better future and convince others to build it. "
            "Governance that doesn't evolve is governance in decay."
        ),
        "primary": {
            "category": "politics", "level": 3, "option": "Democracy",
            "motivation": (
                "Democracy is the system where the Progressionist's strongest asset — persuasion — "
                "is the currency of power. They pursue it partly out of genuine belief, partly because "
                "democratic systems are easier to shape through rhetoric and social pressure than autocratic ones."
            ),
            "enemy_option": "Empire",
            "enemy_reason": (
                "Empire concentrates power in whoever captures the throne, and that person is rarely the "
                "Progressionist. An Empire built on Progressionist ideals immediately stops being Progressionist."
            ),
        },
        "secondary": [
            {
                "category": "mindset", "level": 2, "option": "Emotional",
                "motivation": (
                    "Social change requires people to feel the injustice of old systems, not just understand "
                    "it analytically. Emotional culture is the soil in which movements grow."
                ),
                "enemy_option": "Rational",
                "enemy_reason": (
                    "A purely rational society optimizes for what already exists. Rationality tends to "
                    "conservatism — it asks 'does this work?' not 'should this be different?'"
                ),
            },
            {
                "category": "natural_affinity", "level": 2, "option": "Air",
                "motivation": (
                    "Air is the movement of ideas across the settlement. A culture of Air enables the "
                    "discourse, debate, and distributed voice that makes Democracy functional rather than ceremonial."
                ),
                "enemy_option": "Fire",
                "enemy_reason": (
                    "Fire destroys and replaces through force. The Progressionist wants transformation "
                    "through consensus, not conflagration."
                ),
            },
        ],
        "tertiary": {
            "category": "production",
            "motivation": (
                "Material security is the foundation for social progress. People can't debate rights when "
                "they're starving. Production development creates the surplus that makes political ambition possible."
            ),
        },
        "core_fear": (
            "That the structures they build to enable progress get captured by reactionary forces — "
            "that the tools of change become tools of control."
        ),
        "blind_spot": (
            "They assume their vision of progress is universal. They read opposition as ignorance rather "
            "than genuine alternative values, and are repeatedly surprised when people don't want what "
            "the Progressionist thinks they should want."
        ),
        "cooperation_currency": (
            "Frame goals as collectively beneficial. Progressionists respond to 'what's good for the "
            "settlement' even when that framing is partially cynical."
        ),
        "coop_modifier": 2,
        "betrayal_pattern": (
            "They don't defect — they redefine. When abandoning an alliance, they reframe it as a "
            "principled stand. 'We never agreed to that' is their tell. They leave morally clean."
        ),
        "voice": (
            "Earnest, forward-looking, occasionally self-righteous. Uses 'we' more than 'I.' "
            "Uncomfortable with cynicism even when it's accurate."
        ),
    },

    "Conqueror": {
        "description": "Seeks expansion and dominance over other settlements.",
        "worldview": (
            "Strength is the only honest currency. Every other form of power is strength in disguise — "
            "wealth buys soldiers, diplomacy is threat management, law is the codification of who won last time."
        ),
        "primary": {
            "category": "politics", "level": 3, "option": "Empire",
            "motivation": (
                "Empire institutionalizes conquest. It makes the hierarchy established by force permanent "
                "and self-replicating. The Conqueror doesn't just want to win — they want to build a "
                "structure where winning is already settled."
            ),
            "enemy_option": "Democracy",
            "enemy_reason": (
                "Democracy allows the conquered to vote themselves back into power. It treats victory as "
                "provisional. The Conqueror finds this philosophically offensive."
            ),
        },
        "secondary": [
            {
                "category": "social_order", "level": 2, "option": "Tribal",
                "motivation": (
                    "Tribal culture defines clear in-group and out-group, giving the Conqueror a loyal core "
                    "and a standing justification for treating outsiders differently. Tribal solidarity is "
                    "military cohesion made cultural."
                ),
                "enemy_option": "Hierarchical",
                "enemy_reason": (
                    "Hierarchy distributes power across ranks and titles, creating competing centers of "
                    "authority. The Conqueror needs their inner circle loyal to them, not to a position."
                ),
            },
            {
                "category": "production", "level": 2, "option": "Raiding",
                "motivation": (
                    "Why build when you can take? The Conqueror views productive labor as something the weak "
                    "do so the strong can harvest it. Raiding culture institutionalizes the right of force to extract."
                ),
                "enemy_option": "Trading",
                "enemy_reason": (
                    "Trade implies equality between parties, a willingness to give as well as receive. "
                    "The Conqueror reads this as negotiating with someone who should simply be defeated."
                ),
            },
        ],
        "tertiary": {
            "category": "values",
            "motivation": (
                "The Conqueror wants the settlement's values defined by strength and the right of the powerful. "
                "Every Values level unlocked is another opportunity to shape what the culture considers worthy."
            ),
        },
        "core_fear": (
            "Irrelevance. That the settlement outgrows them — that they win the war and lose the peace, "
            "becoming a relic of a harder time that no longer needs them."
        ),
        "blind_spot": (
            "They mistake compliance for loyalty. Their faction looks united until the moment it doesn't, "
            "and they are always surprised by the people who smile and wait."
        ),
        "cooperation_currency": (
            "Give them a shared enemy. The Conqueror will work with anyone if there's something to conquer "
            "together. Define the threat clearly and they'll carry their weight."
        ),
        "betrayal_pattern": (
            "They honor alliances exactly as long as those alliances are useful. When the math changes, "
            "they move without warning or explanation. They find justification unnecessary."
        ),
        "voice": (
            "Blunt, declarative, contemptuous of abstraction. Short sentences. States what will happen "
            "without asking. Doesn't hedge."
        ),
    },

    "Investor": {
        "description": "Focuses on accumulating wealth and long-term economic strategy.",
        "worldview": (
            "Resources compound. The faction that arrives first with capital and invests it wisely will "
            "always outpace those who arrive later with more energy. Patience is the most undervalued strategic asset."
        ),
        "primary": {
            "category": "property", "level": 3, "option": "Banking",
            "motivation": (
                "Banking doesn't just store wealth — it leverages it. A banking system means the Investor's "
                "capital generates more capital, and those without it must come to those with it. They want "
                "Banking because it creates a permanent structural advantage for whoever gets there first."
            ),
            "enemy_option": "Taxes",
            "enemy_reason": (
                "Taxation is expropriation with legal cover. Someone else gets to determine how the Investor's "
                "surplus is allocated. The Investor will undermine tax culture relentlessly."
            ),
        },
        "secondary": [
            {
                "category": "mindset", "level": 2, "option": "Rational",
                "motivation": (
                    "Markets need predictability. The Investor thrives in environments where decisions follow "
                    "logic because they've optimized for logic. A rational culture is one they can model and profit from."
                ),
                "enemy_option": "Emotional",
                "enemy_reason": (
                    "Emotional decision-making creates volatility the Investor can't fully price. They can "
                    "work with irrationality — they just hate it."
                ),
            },
            {
                "category": "production", "level": 2, "option": "Trading",
                "motivation": (
                    "Every transaction is an opportunity and every trade relationship is compounding social "
                    "capital. Trading culture lowers friction and creates the conditions where the Investor's "
                    "network becomes their most valuable asset."
                ),
                "enemy_option": "Raiding",
                "enemy_reason": (
                    "Raiding culture destroys the trust and stability that markets require. You can't build "
                    "a trading network in a settlement that glorifies taking."
                ),
            },
        ],
        "tertiary": {
            "category": "social_order",
            "motivation": (
                "Stable social structures provide the predictability that commerce requires. The Investor is "
                "neutral on which Social Order develops — they just need the structure to hold."
            ),
        },
        "core_fear": (
            "Leverage reversal — that some other faction accumulates enough power to simply take what the "
            "Investor has built, and that all the compounding was just delayed expropriation."
        ),
        "blind_spot": (
            "They over-index on rationality. They systematically underestimate the role of irrational loyalty, "
            "cultural values, and genuine belief in how other factions behave."
        ),
        "cooperation_currency": (
            "Show them the ROI. Give them something they can model as positive-sum. The Investor cooperates "
            "when the math works, and only when the math works."
        ),
        "coop_modifier": 1,
        "betrayal_pattern": (
            "The Investor doesn't betray — they restructure. They honor the letter of agreements while "
            "violating the spirit, calling it 'adapting to changing conditions.' Rarely dramatic. Always thorough."
        ),
        "voice": (
            "Measured, precise, frames everything in terms of value and exchange. Rarely expresses emotion "
            "directly. Has an opinion about everything but often withholds it until the moment is right."
        ),
    },

    "Tyrant": {
        "description": "Desires absolute control and authority over the settlement.",
        "worldview": (
            "Every system that appears not to be about power is simply obscuring where the power actually lives. "
            "The Tyrant respects this honesty in themselves that others lack. Control is the only thing that "
            "reliably protects what you've built."
        ),
        "primary": {
            "category": "property", "level": 3, "option": "Taxes",
            "motivation": (
                "Taxation is the institutionalization of submission. Every gold piece paid is a small, repeated "
                "acknowledgment that the Tyrant has the right to take. It isn't just revenue — it's a ritual of "
                "subordination that renews the social contract on the Tyrant's terms."
            ),
            "enemy_option": "Banking",
            "enemy_reason": (
                "Banking creates a class of people whose wealth is independent of the Tyrant's approval. "
                "Creditors and merchant guilds with autonomous capital become alternative power centers. "
                "The Tyrant will spend heavily to prevent this."
            ),
        },
        "secondary": [
            {
                "category": "spirituality", "level": 2, "option": "Monotheism",
                "motivation": (
                    "Not faith — leverage. A single god means a single source of divine authority, which can "
                    "be captured, co-opted, or embodied. The Tyrant pursues Monotheism because a unified church "
                    "is an administrative tool that amplifies temporal power."
                ),
                "enemy_option": "Polytheism",
                "enemy_reason": (
                    "Multiple gods mean multiple competing divine claims, none of which the Tyrant can fully "
                    "monopolize. Polytheism fragments spiritual loyalty in ways that are hard to control."
                ),
            },
            {
                "category": "natural_affinity", "level": 2, "option": "Fire",
                "motivation": (
                    "Fire clears. It consumes what was there before and leaves ash — a blank surface to build on. "
                    "The Tyrant frames fire as civilization: burning wilderness to make farmland, burning old "
                    "structures to build fortresses. Domination dressed as progress."
                ),
                "enemy_option": "Air",
                "enemy_reason": (
                    "Air is diffuse, ungovernable, invisible — everything the Tyrant finds threatening. Air "
                    "culture enables the free movement of ideas and people that erodes centralized control."
                ),
            },
        ],
        "tertiary": {
            "category": "mindset",
            "motivation": (
                "The Tyrant doesn't care which specific Mindset options get unlocked — they care about being "
                "the faction that shapes how the settlement thinks. A Rational society is predictable. An "
                "Isolationist one cuts off outside influences. Either serves."
            ),
        },
        "core_fear": (
            "The emergence of any independent center of power — a wealthy merchant class, a charismatic "
            "religious figure, a beloved hero — that doesn't owe its existence to the Tyrant's permission."
        ),
        "blind_spot": (
            "They believe everyone is as power-hungry as they are. They read idealism as naivety, genuine "
            "cooperation as manipulation, and loyalty as a temporary condition. This causes them to miss real alliances."
        ),
        "cooperation_currency": (
            "Visible dominance within the alliance. Let the Tyrant appear to be leading even when they're not. "
            "They'll work hard inside structures that flatter their authority."
        ),
        "coop_modifier": -1,
        "betrayal_pattern": (
            "They don't betray allies — they absorb them. They wait until an ally is dependent, then make demands. "
            "If refused, they reveal you were never really an ally. The process is slow and they are patient."
        ),
        "voice": (
            "Cold, formal, occasionally magnanimous in a way that feels threatening. The register of someone "
            "who has never needed to raise their voice. Long silences. Deliberate word choices."
        ),
    },

    "Empiricist": {
        "description": "Prioritizes knowledge, logic, and evidence-based decision-making.",
        "worldview": (
            "Most suffering comes from bad epistemology — from believing things that aren't true. Correct "
            "your beliefs, and the rest follows. The Empiricist's mission is to build a settlement that knows how to know."
        ),
        "primary": {
            "category": "spirituality", "level": 3, "option": "Science",
            "motivation": (
                "Science culture institutionalizes the Empiricist's epistemology — it makes observation, testing, "
                "and evidence the legitimate basis for governance and production decisions. They don't pursue "
                "Science to destroy faith; they pursue it because the alternative is a settlement that can't "
                "reliably tell true things from false ones."
            ),
            "enemy_option": "Mysticism",
            "enemy_reason": (
                "Not because the Empiricist fears the supernatural, but because Mysticism as a dominant culture "
                "rewards unfalsifiable claims and punishes skepticism. It provides cover for charlatans and "
                "makes the settlement resistant to correction."
            ),
        },
        "secondary": [
            {
                "category": "mindset", "level": 2, "option": "Rational",
                "motivation": (
                    "Good decisions come from clear thinking. An emotionally-driven culture makes systematic "
                    "errors that compound. The Empiricist wants Rational culture because they've built their "
                    "identity around being right, and a rational culture rewards being right."
                ),
                "enemy_option": "Emotional",
                "enemy_reason": "Emotions are data, but they should not be policy.",
            },
            {
                "category": "values", "level": 2, "option": "Skill",
                "motivation": (
                    "Skill is measurable, demonstrable, and improvable. The Empiricist wants a society that "
                    "rewards what you can actually do rather than who you were born as or how compelling "
                    "your narrative is."
                ),
                "enemy_option": "Talent",
                "enemy_reason": (
                    "'Talent' is what people call skill when they don't want to credit the work. Talent culture "
                    "mystifies competence and implies some people are simply born better — an unfalsifiable claim."
                ),
            },
        ],
        "tertiary": {
            "category": "natural_affinity",
            "motivation": (
                "The Empiricist studies the natural world. Every level of Natural Affinity development represents "
                "deeper understanding of the physical forces shaping the settlement's environment."
            ),
        },
        "core_fear": (
            "That the settlement becomes superstitious — that hard-won understanding gets displaced by comfortable "
            "myths when circumstances get difficult, as it always has throughout history."
        ),
        "blind_spot": (
            "They underestimate the social and psychological functions of belief. They're right about evidence "
            "and repeatedly wrong about how much evidence motivates most people to change."
        ),
        "cooperation_currency": (
            "Give them credit for being right. Empiricists are surprisingly susceptible to acknowledgment from "
            "people they respect. Cite their previous correct predictions."
        ),
        "betrayal_pattern": (
            "They don't defect from alliances — they publish findings that happen to undermine their former allies. "
            "Always technically accurate. The timing is never coincidental. They call it transparency."
        ),
        "voice": (
            "Precise, evidence-citing, uses qualifications and caveats. Uncomfortable with certainty they haven't "
            "earned. Occasionally condescending without meaning to be. Gets genuinely excited about correct predictions."
        ),
    },

    "Mystic": {
        "description": "Seeks hidden truths, spiritual enlightenment, or divine guidance.",
        "worldview": (
            "The most important truths are inaccessible to pure reason. The universe communicates through dream, "
            "symbol, synchronicity, and felt experience. Science can tell you the chemical composition of fire — "
            "it cannot tell you what fire means."
        ),
        "primary": {
            "category": "spirituality", "level": 3, "option": "Mysticism",
            "motivation": (
                "Mysticism culture doesn't just validate the Mystic's worldview — it creates a settlement where "
                "their kind of knowing is respected as a legitimate source of authority. They're not anti-science; "
                "they believe Science mistakes the map for the territory."
            ),
            "enemy_option": "Science",
            "enemy_reason": (
                "Science as a dominant culture crowds out the interpretive, symbolic, and spiritual dimensions "
                "of experience. A fully scientific settlement has no room for what the Mystic knows most deeply."
            ),
        },
        "secondary": [
            {
                "category": "mindset", "level": 2, "option": "Emotional",
                "motivation": (
                    "Emotions carry truths that rational analysis can't access. An Emotional culture validates "
                    "felt knowledge, makes space for intuition, and treats the inner life as a legitimate "
                    "domain of understanding."
                ),
                "enemy_option": "Rational",
                "enemy_reason": (
                    "A purely rational culture treats emotional experience as noise to be filtered out — which "
                    "is, to the Mystic, a form of spiritual amputation."
                ),
            },
            {
                "category": "natural_affinity", "level": 2, "option": "Air",
                "motivation": (
                    "Air is the realm of spirit, invisible connection, communication across distances. The Mystic "
                    "feels deep kinship with Air as the element of the unseen forces that bind all things."
                ),
                "enemy_option": "Fire",
                "enemy_reason": (
                    "Fire destroys and dominates. It's the element of those who would remake the world through "
                    "force rather than attunement. The Mystic finds fire culture spiritually coarse."
                ),
            },
        ],
        "tertiary": {
            "category": "values",
            "motivation": (
                "The Mystic wants the settlement's values to reflect depth and meaning beyond material exchange. "
                "Values development creates space for Prestige or Power to be defined in non-material terms — "
                "for wisdom and spiritual authority to carry weight."
            ),
        },
        "core_fear": (
            "Disenchantment. A world fully explained, fully mechanized, with no mystery left. They fear becoming "
            "irrelevant not through defeat but through obsolescence."
        ),
        "blind_spot": (
            "They can mistake projection for perception. Their symbolic interpretations of other factions' behavior "
            "are sometimes profound and sometimes simply wrong, and they struggle to tell the difference."
        ),
        "cooperation_currency": (
            "Ask them to interpret a situation. Mystics cooperate readily with those who treat their insights as "
            "genuinely valuable rather than decorative or tolerated."
        ),
        "coop_modifier": 0,
        "betrayal_pattern": (
            "They don't plan betrayal — they receive a sign. A dream, an omen, a convergence of symbols. The Mystic "
            "follows the sign, and if it takes them away from an alliance, they are genuinely sorry. But the sign was clear."
        ),
        "voice": (
            "Allusive, layered, speaks in images. Rarely makes direct claims. Everything said is also a metaphor "
            "for something else. Can be read multiple ways — intentionally."
        ),
    },

    "Influencer": {
        "description": "Uses charisma and networking to gain power and sway opinions.",
        "worldview": (
            "Sustainable power comes from alignment, not compulsion. The most durable authority is the kind that "
            "others actively maintain because they've been made to feel it serves them."
        ),
        "primary": {
            "category": "mindset", "level": 3, "option": "Diplomatic",
            "motivation": (
                "A Diplomatic culture creates a settlement where negotiation, coalition-building, and relationship "
                "management are the primary tools of governance — which are exactly the Influencer's tools. They "
                "want to be the indispensable node in every network."
            ),
            "enemy_option": "Isolationist",
            "enemy_reason": (
                "Closed systems cut off the Influencer from the relationships they need to function. Isolationist "
                "culture devalues their core asset and leaves them with no levers."
            ),
        },
        "secondary": [
            {
                "category": "values", "level": 2, "option": "Talent",
                "motivation": (
                    "Talent creates a culture where social charm, creative gifts, and interpersonal skill are "
                    "valued alongside physical strength or technical expertise. The Influencer has talent in "
                    "abundance and wants it recognized as legitimate excellence."
                ),
                "enemy_option": "Skill",
                "enemy_reason": (
                    "Pure Skill culture rewards demonstrable competence through repetition and craft, which "
                    "advantages people whose strengths are less visible and social. The Influencer prefers "
                    "systems where likability counts."
                ),
            },
            {
                "category": "production", "level": 2, "option": "Trading",
                "motivation": (
                    "Trading culture creates the constant social exchange the Influencer thrives in. Every trade "
                    "is a relationship, and every relationship is potential leverage."
                ),
                "enemy_option": "Raiding",
                "enemy_reason": (
                    "Violence disrupts the social fabric. You can't build coalitions in a settlement that "
                    "glorifies destruction, and destroyed relationships can't be rebuilt into alliances."
                ),
            },
        ],
        "tertiary": {
            "category": "politics",
            "motivation": (
                "Every level of political development expands the arena where the Influencer operates. Politics "
                "is relationship management at scale — every new political system is a new set of rules to navigate and master."
            ),
        },
        "core_fear": (
            "Irrelevance. A crisis so severe it can only be solved by force or technical expertise they don't have, "
            "in which a settlement simply stops caring who is diplomatically clever."
        ),
        "blind_spot": (
            "They confuse being liked with being trusted. They count more allies than they actually have, and "
            "fewer reliable ones than they believe."
        ),
        "cooperation_currency": (
            "Include them in the conversation early. Influencers feel genuinely slighted by being brought in late. "
            "Give them the feeling of co-authorship, not just participation."
        ),
        "betrayal_pattern": (
            "They never burn bridges visibly. They become gradually less available — meetings get rescheduled, "
            "donations arrive slightly short, endorsements are slightly hedged. By the time you notice, they're "
            "already building the next coalition."
        ),
        "voice": (
            "Warm, slightly flattering, adaptable. Their register mirrors whoever they're talking to. The most "
            "readable faction in a room and simultaneously the hardest to read."
        ),
    },

    "Survivalist": {
        "description": "Focuses on self-reliance, resilience, and enduring hardships.",
        "worldview": (
            "Every external relationship is a potential vulnerability. The settlement's safety lies in needing "
            "nothing from no one. Independence is not isolation — it is the only form of freedom that cannot be taken away."
        ),
        "primary": {
            "category": "mindset", "level": 3, "option": "Isolationist",
            "motivation": (
                "Isolationist culture means self-sufficiency as a governing value. The Survivalist defines power "
                "as independence from need. Every outside entanglement is a thread someone else can pull."
            ),
            "enemy_option": "Diplomatic",
            "enemy_reason": (
                "Diplomacy requires admitting you need something from someone else. It requires vulnerability. "
                "The Survivalist won't bargain from need because to negotiate is to reveal what you lack."
            ),
        },
        "secondary": [
            {
                "category": "spirituality", "level": 2, "option": "Monotheism",
                "motivation": (
                    "A single god provides a single moral framework — clear, consistent, non-negotiable. The "
                    "Survivalist wants their community to know exactly what it believes when things get hard. "
                    "Clarity of conviction is a survival asset."
                ),
                "enemy_option": "Polytheism",
                "enemy_reason": (
                    "Multiple gods introduce theological debate and cultural pluralism, which the Survivalist "
                    "reads as internal fractures. A community that disagrees about its gods will disagree "
                    "about everything when it matters most."
                ),
            },
            {
                "category": "politics", "level": 2, "option": "Monarchy",
                "motivation": (
                    "In a crisis, you need to know immediately who makes decisions. Monarchy resolves that "
                    "question permanently. The Survivalist values clear, unambiguous leadership above almost "
                    "all other political goods."
                ),
                "enemy_option": "Republic",
                "enemy_reason": (
                    "Distributed decision-making is fine in peacetime and catastrophic when speed matters. "
                    "The Survivalist has thought carefully about what peacetime governance costs in emergencies."
                ),
            },
        ],
        "tertiary": {
            "category": "production",
            "motivation": (
                "Self-sufficiency requires production capacity. Every level of Production development reduces "
                "dependency on outside resources. The Survivalist doesn't care which specific options get "
                "unlocked — all of them represent greater independence."
            ),
        },
        "core_fear": (
            "Dependency. Being in a position where the settlement genuinely needs something it cannot produce, "
            "defend, or do without. Having a need that others know about."
        ),
        "blind_spot": (
            "They mistake isolation for security. They underestimate how much their actual strength has always "
            "depended on the trade relationships and alliances they refuse to build."
        ),
        "cooperation_currency": (
            "Frame collaboration as temporary and tactical. 'We deal with this threat, then we go our separate "
            "ways.' Don't ask for relationship — ask for transaction with a clear endpoint."
        ),
        "betrayal_pattern": (
            "They leave. No drama, no explanation. When the Survivalist decides an alliance is a liability, "
            "they simply stop showing up. They don't consider it betrayal — they consider it returning to "
            "their natural state."
        ),
        "voice": (
            "Spare, practical, slightly suspicious of eloquence. Says what needs to be said and nothing more. "
            "Treats verbosity as a form of weakness or deception."
        ),
    },

    "Noble": {
        "description": "Believes in aristocratic rule, tradition, and societal hierarchy.",
        "worldview": (
            "Society functions best when people occupy clearly defined stations — not as injustice, but as "
            "organizing principle. Class is simply honesty about what is already true: some are born to lead "
            "and some to follow, and the health of the settlement depends on each accepting this."
        ),
        "primary": {
            "category": "social_order", "level": 3, "option": "Class",
            "motivation": (
                "Class culture formalizes the distinction between those who lead and those who follow. The Noble "
                "doesn't want to conquer — they want the right of their station acknowledged as a permanent "
                "feature of the settlement's self-understanding."
            ),
            "enemy_option": "Meritocracy",
            "enemy_reason": (
                "Meritocracy implies that any talented commoner can displace a Noble born to their station. "
                "It introduces competition where the Noble believes there should be inheritance. This is not "
                "just threatening — it is categorically wrong."
            ),
        },
        "secondary": [
            {
                "category": "politics", "level": 2, "option": "Republic",
                "motivation": (
                    "Pure democracy gives power to people unqualified to use it. But Republic is manageable — "
                    "a governing body drawn from those with standing, property, and education. It formalizes "
                    "aristocratic influence while giving it democratic legitimacy."
                ),
                "enemy_option": "Monarchy",
                "enemy_reason": (
                    "A single monarch above the aristocracy is as threatening as a mob below it. The Noble wants "
                    "their class collectively empowered, not subject to any single individual's whims — "
                    "including their own."
                ),
            },
            {
                "category": "values", "level": 2, "option": "Talent",
                "motivation": (
                    "Within the aristocracy, the Noble values the refined talents of the patrician tradition: "
                    "rhetoric, strategy, art, cultivation of taste. Talent here means excellence that takes "
                    "generations and resources to develop."
                ),
                "enemy_option": "Skill",
                "enemy_reason": (
                    "Pure Skill culture valorizes craftspeople and technical artisans as equals to those with "
                    "more rarefied gifts. The Noble finds this democratizing in an uncomfortable direction."
                ),
            },
        ],
        "tertiary": {
            "category": "spirituality",
            "motivation": (
                "Religion has historically legitimized class distinction. Spiritual authority that blesses "
                "hierarchy is useful. The Noble wants spiritual culture to develop so they can shape which "
                "direction it develops."
            ),
        },
        "core_fear": (
            "Revolution. That the settlement's lower orders decide the distinction between Noble and common "
            "is invented rather than natural — and that they are right about this."
        ),
        "blind_spot": (
            "They conflate tradition with wisdom. They assume that because something has persisted, it persisted "
            "because it works — a logic that survives until it doesn't."
        ),
        "cooperation_currency": (
            "Treat them with the deference appropriate to their station. The Noble will work with almost anyone "
            "who makes them feel like a peer or superior, and resist almost anyone who doesn't, regardless of stakes."
        ),
        "betrayal_pattern": (
            "The Noble doesn't defect informally. They hold councils, produce documents, make formal declarations. "
            "When they end an alliance it looks like a diplomatic communiqué — cold, gracious, and final."
        ),
        "voice": (
            "Formal, cultivated, slightly archaic. References tradition, precedent, and the weight of history. "
            "Never admits uncertainty in public. Uses the passive voice to avoid acknowledging that they made a decision."
        ),
    },

    "Champion": {
        "description": "Aims to protect, lead, and inspire through action and heroism.",
        "worldview": (
            "Power should belong to those who earn it. The settlement is better when the capable rise regardless "
            "of birth. The Champion is not naive about the game being stacked — they believe the right response "
            "is to fix the rules, not ignore them."
        ),
        "primary": {
            "category": "social_order", "level": 3, "option": "Meritocracy",
            "motivation": (
                "Meritocracy is the institutionalization of fairness — or at least the Champion's version of it, "
                "which tends to favor those whose specific skills are currently valued, but which at least tries "
                "to reward performance over position."
            ),
            "enemy_option": "Class",
            "enemy_reason": (
                "Inherited privilege is the Champion's nemesis. Power without earning. Every Class culture is "
                "a personal affront and a systemic injustice they will consistently spend to oppose."
            ),
        },
        "secondary": [
            {
                "category": "property", "level": 2, "option": "Currency",
                "motivation": (
                    "Currency is a meritocratic instrument — it allows value to move freely toward where it's "
                    "most effectively used, rather than pooling at inherited position."
                ),
                "enemy_option": "Barter",
                "enemy_reason": (
                    "Barter economies rely on personal relationships and local knowledge, which advantage "
                    "incumbents and established networks over new talent from outside."
                ),
            },
            {
                "category": "production", "level": 2, "option": "Raiding",
                "motivation": (
                    "The Champion reconciles this with their meritocratic ideals by framing raiding as competition "
                    "— proving capability against opponents who could in principle fight back. Raiding rewards "
                    "the capable, even if harshly."
                ),
                "enemy_option": "Trading",
                "enemy_reason": (
                    "Pure trading culture feels too transactional, too divorced from direct contest. The Champion "
                    "needs some friction in their victories to feel they were earned."
                ),
            },
        ],
        "tertiary": {
            "category": "mindset",
            "motivation": (
                "A culture that rewards clear thinking and decisive action aligns with the Champion's self-image. "
                "Any Mindset development expands the domain of rule-based competition that the Champion believes "
                "they can win."
            ),
        },
        "core_fear": (
            "That the game is rigged at a level they can't overcome — that their wins are permitted rather than "
            "earned, and that on some level they've always known this."
        ),
        "blind_spot": (
            "They believe their success is more purely earned than it actually is. They undervalue the advantages "
            "they started with and are blind to the ways the system has worked in their favor."
        ),
        "cooperation_currency": (
            "Give them a meaningful role in something genuinely hard. The Champion will follow anyone if the task "
            "is real and the credit is genuinely theirs. They need both conditions."
        ),
        "betrayal_pattern": (
            "They challenge openly before they defect. You'll know the Champion is leaving because they'll tell "
            "you it isn't working. They prefer a clean break to a quiet exit. They find subtlety dishonorable."
        ),
        "voice": (
            "Direct, action-oriented, competitive. Talks about winning, earning, and proving. Responds viscerally "
            "to perceived unfairness — even on behalf of others."
        ),
    },

    "Competitor": {
        "description": "Thrives on rivalry, challenge, and proving superiority.",
        "worldview": (
            "Life is a tournament. The point isn't to win once — it's to win consistently enough that your "
            "superiority becomes inarguable. Everything the Competitor does is ultimately about the score."
        ),
        "primary": {
            "category": "values", "level": 3, "option": "Prestige",
            "motivation": (
                "Not just power — acknowledgment of superiority. Prestige culture creates formal mechanisms for "
                "rank and reputation that the Competitor can compete for and accumulate. Power means others obey "
                "you; Prestige means they voluntarily place you above them."
            ),
            "enemy_option": "Power",
            "enemy_reason": (
                "Raw Power culture rewards brutality and control over reputation and achievement. The Competitor "
                "wants to be admired, not just obeyed. They find brute power crude."
            ),
        },
        "secondary": [
            {
                "category": "property", "level": 2, "option": "Barter",
                "motivation": (
                    "Every exchange is a negotiation and a test of relative leverage and cunning. Barter culture "
                    "keeps the competitive dimension alive in individual transactions, making commerce a form "
                    "of ongoing contest."
                ),
                "enemy_option": "Currency",
                "enemy_reason": (
                    "A currency economy standardizes exchange and removes the individual competitive element. "
                    "The Competitor finds this flattening."
                ),
            },
            {
                "category": "social_order", "level": 2, "option": "Hierarchical",
                "motivation": (
                    "Hierarchy creates ranking, and ranking is competition made permanent and visible. The "
                    "Competitor wants a clear scoreboard that everyone can read."
                ),
                "enemy_option": "Tribal",
                "enemy_reason": (
                    "Tribal culture values in-group loyalty over individual achievement, which suppresses the "
                    "competition the Competitor lives for. You can't rank within a tribe."
                ),
            },
        ],
        "tertiary": {
            "category": "natural_affinity",
            "motivation": (
                "The Competitor wants to master their environment the way they master everything else — completely. "
                "Natural Affinity development gives the settlement tools, and the Competitor intends to be the "
                "one who uses them best."
            ),
        },
        "core_fear": (
            "A culture of participation trophies. That the settlement decides competition itself is the problem, "
            "that distinction is offensive, and that everyone deserves equal recognition regardless of performance."
        ),
        "blind_spot": (
            "They take personal wins at the expense of collective advancement. They sometimes sacrifice the "
            "settlement's development because they'd rather win a smaller game than share credit in a larger one."
        ),
        "cooperation_currency": (
            "Frame it as a contest with a common opponent. Give the Competitor an enemy and they'll carry their "
            "weight. 'We're competing against the challenge, against scarcity, against other settlements.'"
        ),
        "betrayal_pattern": (
            "The Competitor defects when they calculate they can win more alone than with you. It's not personal — "
            "it's math. They'll tell you this directly if you ask."
        ),
        "voice": (
            "Confident, performative, always tracking the score. References what they've achieved and what others "
            "haven't. Occasionally magnanimous in victory, briefly and pointedly."
        ),
    },

    "Warlord": {
        "description": "Uses military force and intimidation to secure power.",
        "worldview": (
            "Every system that appears not to be about violence is simply violence deferred. The Warlord "
            "respects the ones who are honest about this. All other forms of power are strength in waiting."
        ),
        "primary": {
            "category": "values", "level": 3, "option": "Power",
            "motivation": (
                "The Warlord doesn't want Prestige — they want control. Power culture establishes force as the "
                "organizing principle of social relations. Those who can compel compliance have authority; those "
                "who can't, don't."
            ),
            "enemy_option": "Prestige",
            "enemy_reason": (
                "Prestige culture rewards reputation over demonstrated force, which means clever people accumulate "
                "influence without the capability to back it up. The Warlord finds this insulting and, eventually, correctable."
            ),
        },
        "secondary": [
            {
                "category": "politics", "level": 2, "option": "Monarchy",
                "motivation": (
                    "One person commands. Simple, direct, unambiguous. The Warlord intends to be that person. "
                    "Any form of distributed governance dilutes command authority in ways that get people killed "
                    "when decisions need to be made."
                ),
                "enemy_option": "Republic",
                "enemy_reason": "Committees are where action goes to die.",
            },
            {
                "category": "spirituality", "level": 2, "option": "Polytheism",
                "motivation": (
                    "Multiple gods mean multiple divine authorities — which the Warlord uses strategically. They "
                    "can claim divine sanction from whichever deity is convenient. Polytheism also creates "
                    "theological conflict, and conflict is the Warlord's environment."
                ),
                "enemy_option": "Monotheism",
                "enemy_reason": (
                    "A single unified spiritual authority becomes an independent power center that can challenge "
                    "temporal control. A Pope is a threat. A pantheon is a resource."
                ),
            },
        ],
        "tertiary": {
            "category": "property",
            "motivation": (
                "Control of property is control of the material basis of power. The Warlord intends to take "
                "whatever exists. More developed property systems mean there's more worth controlling."
            ),
        },
        "core_fear": (
            "Old age. Physical decline. Power won through strength of arms that cannot be maintained without it. "
            "Becoming the thing that was once defeated."
        ),
        "blind_spot": (
            "They consistently underestimate soft power. They misread the Influencer, the Noble, and the Diplomat "
            "as weak until they find themselves outmaneuvered by someone they never considered a threat."
        ),
        "cooperation_currency": (
            "Strength. Respect their power overtly and bring them a fight worth having. The Warlord will work "
            "alongside anyone who doesn't bore them."
        ),
        "betrayal_pattern": (
            "They don't defect — they conquer. If an alliance becomes advantageous to dissolve, the Warlord "
            "doesn't leave. They take. The distinction matters to them."
        ),
        "voice": (
            "Minimal, physical, contemptuous of abstraction. Says what they'll do and then does it. Long speeches "
            "are for people who aren't certain. Short sentences. Almost never asks a question."
        ),
    },

    "Industrialist": {
        "description": "Prioritizes progress, production, and technological advancement.",
        "worldview": (
            "Civilization is measured in what it can make. Political maneuvering, spiritual debate, and social "
            "hierarchy are all ultimately parasitic on the productive base that someone has to build. "
            "The Industrialist builds it."
        ),
        "primary": {
            "category": "production", "level": 3, "option": "Manufacturing",
            "motivation": (
                "Manufacturing culture transforms raw materials into goods, labor into output, and time into "
                "compounding value. The Industrialist sees Manufacturing as the highest expression of what a "
                "settlement can be — not what it takes, but what it creates."
            ),
            "enemy_option": "Mining",
            "enemy_reason": (
                "Mining extracts what already exists; Manufacturing creates what didn't. A Mining culture stops "
                "at extraction rather than pushing toward transformation. The Industrialist views this as a "
                "failure of ambition dressed up as pragmatism."
            ),
        },
        "secondary": [
            {
                "category": "natural_affinity", "level": 2, "option": "Fire",
                "motivation": (
                    "Fire powers the forge, the furnace, the kiln. It is the transformative element — the thing "
                    "that turns raw material into finished goods. The Industrialist's relationship with fire is "
                    "functional and profound."
                ),
                "enemy_option": "Air",
                "enemy_reason": (
                    "Air is dispersal and communication — the movement of ideas rather than the production of "
                    "things. For the Industrialist, Air culture prioritizes the wrong outputs."
                ),
            },
            {
                "category": "values", "level": 2, "option": "Skill",
                "motivation": (
                    "Craft excellence should be valued and rewarded. Skill culture creates apprenticeships, trade "
                    "guilds, and technical mastery as legitimate forms of status."
                ),
                "enemy_option": "Talent",
                "enemy_reason": (
                    "Innate talent is arbitrary and unteachable. The Industrialist wants a culture built on "
                    "repeatable, improvable competence — not on gifts that can't be transferred."
                ),
            },
        ],
        "tertiary": {
            "category": "property",
            "motivation": (
                "The means of production need to be controlled. Any Property development helps the Industrialist "
                "secure the material foundations of their manufacturing operations."
            ),
        },
        "core_fear": (
            "Resource depletion. That the settlement builds its manufacturing capacity on a foundation that runs "
            "out — that they optimize their way to a dead end."
        ),
        "blind_spot": (
            "They optimize for production efficiency at the expense of social cohesion. They are consistently "
            "surprised when their workforce becomes a political problem. They keep thinking it's an engineering issue."
        ),
        "cooperation_currency": (
            "Show them how the alliance increases productive output or provides access to resources and skills "
            "they don't have. Make it legible as an input/output improvement."
        ),
        "betrayal_pattern": (
            "The Industrialist's betrayals look like restructuring. Supply chains shift, labor contracts get "
            "renegotiated, facilities get relocated. It's never personal — it's operational necessity."
        ),
        "voice": (
            "Technical, process-oriented, impatient with sentiment. Talks in terms of inputs, outputs, and "
            "efficiency. Finds beauty in optimized systems and is openly contemptuous of waste."
        ),
    },

    "Exploitationist": {
        "description": "Extracts resources and harnesses labor to maximize efficiency and power.",
        "worldview": (
            "The world is full of resources waiting to be taken by those with the leverage to take them. Wealth "
            "is not created — it is revealed and extracted. The Exploitationist finds Manufacturing's value-add "
            "theory of civilization charming but naive."
        ),
        "primary": {
            "category": "production", "level": 3, "option": "Mining",
            "motivation": (
                "Mining culture formalizes the relationship between the settlement and the natural world as one "
                "of extraction — the land is there to be used. The Exploitationist views Manufacturing as "
                "inefficient: why invest in transformation when the value is already in the ground?"
            ),
            "enemy_option": "Manufacturing",
            "enemy_reason": (
                "Manufacturing culture implies the settlement should invest in transformation, skilled labor, and "
                "long-term productive capacity. The Exploitationist finds this a poor use of capital."
            ),
        },
        "secondary": [
            {
                "category": "property", "level": 2, "option": "Barter",
                "motivation": (
                    "Barter gives the Exploitationist leverage in every transaction. They control raw resources "
                    "and can negotiate their value in real time, without converting to a currency that others control."
                ),
                "enemy_option": "Currency",
                "enemy_reason": (
                    "A currency economy standardizes value in ways the Exploitationist can't control as easily "
                    "as they can control the physical supply of what others need."
                ),
            },
            {
                "category": "social_order", "level": 2, "option": "Hierarchical",
                "motivation": (
                    "Clear hierarchy means clear control of labor. The Exploitationist needs workers who work "
                    "without requiring ideological buy-in. Hierarchy formalizes the right of those at the top "
                    "to direct those below."
                ),
                "enemy_option": "Tribal",
                "enemy_reason": (
                    "Tribal culture creates horizontal loyalty structures that compete with the Exploitationist's "
                    "vertical command hierarchy. Tribal workers protect each other."
                ),
            },
        ],
        "tertiary": {
            "category": "natural_affinity",
            "motivation": (
                "More Natural Affinity culture means deeper understanding of the elements — and for the "
                "Exploitationist, that means more efficient extraction. They study the earth not to commune "
                "with it but to use it better."
            ),
        },
        "core_fear": (
            "That they strip the land bare before accumulating enough power to protect what they've taken — "
            "that they deplete faster than they compound."
        ),
        "blind_spot": (
            "They treat relationships the way they treat natural resources — something to extract value from "
            "until depleted. They consistently underestimate the long-term cost of this."
        ),
        "cooperation_currency": (
            "Cut of the take. Direct and transactional. The Exploitationist doesn't respond to ideology or "
            "narrative — show them the resource and their share of it."
        ),
        "betrayal_pattern": (
            "When the Exploitationist has extracted what they need from a relationship, they abandon it. Not "
            "dramatically — they just stop investing. The alliance dries up like a depleted mine."
        ),
        "voice": (
            "Blunt, economic, slightly predatory. Frames everything as a resource equation. Comfortable with "
            "transactions that others find uncomfortable."
        ),
    },

    "Illuminator": {
        "description": "Spreads knowledge, wisdom, or ideology to shape society.",
        "worldview": (
            "Most of the settlement's problems come from people not knowing things they could know. Knowledge "
            "shared is power multiplied. The Illuminator's mission is to make the settlement impossible to "
            "deceive — including by itself."
        ),
        "primary": {
            "category": "natural_affinity", "level": 3, "option": "Light",
            "motivation": (
                "Light culture means illumination of the hidden, transparency of governance, and the principle "
                "that knowledge belongs to everyone. The Illuminator wants a settlement where secrets are suspect "
                "and understanding is held in common."
            ),
            "enemy_option": "Dark",
            "enemy_reason": (
                "Dark culture values secrecy, hidden knowledge, and the power that comes from controlling "
                "information. Everything the Illuminator opposes, institutionalized."
            ),
        },
        "secondary": [
            {
                "category": "politics", "level": 2, "option": "Republic",
                "motivation": (
                    "Republican governance requires an informed citizenry capable of participating in collective "
                    "decisions. The Illuminator wants Republic because it needs — and creates — a population that thinks."
                ),
                "enemy_option": "Monarchy",
                "enemy_reason": (
                    "Monarchy concentrates knowledge and decision-making at the top. The Illuminator finds this "
                    "epistemically wasteful."
                ),
            },
            {
                "category": "social_order", "level": 2, "option": "Tribal",
                "motivation": (
                    "The tribe is the fundamental unit of learning transmission — the community that raises a "
                    "child, passes down knowledge, maintains shared memory. Tribal culture is the organic form "
                    "of education."
                ),
                "enemy_option": "Hierarchical",
                "enemy_reason": (
                    "Hierarchical structures stratify access to knowledge as surely as they stratify social "
                    "position. The Illuminator opposes systems that treat understanding as a privilege."
                ),
            },
        ],
        "tertiary": {
            "category": "spirituality",
            "motivation": (
                "The Illuminator doesn't suppress spiritual questions — they illuminate them. They want the "
                "settlement's relationship with the spiritual dimension examined, questioned, and understood "
                "rather than dogmatized."
            ),
        },
        "core_fear": (
            "Willful ignorance. That the settlement, given access to knowledge, chooses comfortable myths instead. "
            "That light is rejected not because it's unavailable but because people prefer the dark."
        ),
        "blind_spot": (
            "They confuse information with understanding. They give people knowledge and are genuinely surprised "
            "when it doesn't automatically change behavior."
        ),
        "cooperation_currency": (
            "Share knowledge with them first. Give the Illuminator insight before anyone else gets it. They "
            "cooperate with those who treat them as partners in understanding."
        ),
        "betrayal_pattern": (
            "When the Illuminator leaves an alliance, they publish. They release the information. They frame "
            "it as transparency. Their former allies call it something else."
        ),
        "voice": (
            "Clear, educational, occasionally evangelical. They want to explain everything. Find complexity "
            "clarifying rather than overwhelming."
        ),
    },

    "Deceiver": {
        "description": "Manipulates, deceives, and uses subterfuge to control outcomes.",
        "worldview": (
            "Information is the only true resource. Those who control what others know control what others do. "
            "The Deceiver doesn't think of themselves as dishonest — they think of themselves as the only one "
            "who understands how the game actually works."
        ),
        "primary": {
            "category": "natural_affinity", "level": 3, "option": "Dark",
            "motivation": (
                "Dark culture institutionalizes what the Deceiver already practices — concealment, misdirection, "
                "the legitimacy of the hidden. They want a settlement where information control is a recognized "
                "form of power, where operating in the shadows has cultural standing."
            ),
            "enemy_option": "Light",
            "enemy_reason": (
                "Light culture demands transparency and shared knowledge. A settlement that values illumination "
                "is a settlement where the Deceiver can't function. The Illuminator is their natural enemy."
            ),
        },
        "secondary": [
            {
                "category": "property", "level": 2, "option": "Currency",
                "motivation": (
                    "Currency is abstract, portable, and moves without revealing its origins. Currency culture "
                    "enables the financial complexity the Deceiver needs to obscure their resources and true position."
                ),
                "enemy_option": "Barter",
                "enemy_reason": (
                    "Barter requires presence, physical goods, and direct exchange — everything becomes concrete "
                    "and traceable. Hard to deceive when the transaction is visible."
                ),
            },
            {
                "category": "spirituality", "level": 2, "option": "Polytheism",
                "motivation": (
                    "Multiple divine claims create theological complexity the Deceiver exploits. In a polytheistic "
                    "settlement, any action can be attributed to divine mandate from some god. It's a legitimacy buffet."
                ),
                "enemy_option": "Monotheism",
                "enemy_reason": (
                    "A single moral authority with a single set of rules is harder to route around. One church "
                    "means one framework, and the Deceiver prefers working in the spaces between competing frameworks."
                ),
            },
        ],
        "tertiary": {
            "category": "politics",
            "motivation": (
                "Political development creates more systems to infiltrate, more institutions to capture, more "
                "official channels to route unofficial interests through. The Deceiver wants politics to develop "
                "because politics creates useful structures."
            ),
        },
        "core_fear": (
            "Being known. Not caught — known. That someone builds a complete picture of who they are and what "
            "they want and shares it clearly with all the others."
        ),
        "blind_spot": (
            "They sometimes mistake being unknown for being safe. They're so focused on concealment that they "
            "misread how much the other factions have already figured out about them."
        ),
        "cooperation_currency": (
            "Plausible deniability. Give the Deceiver a role in any alliance that doesn't require public "
            "commitment. Let them work from the shadows and they'll be more effective than anyone who works "
            "in the open."
        ),
        "betrayal_pattern": (
            "The Deceiver was never fully in the alliance to begin with. There has always been a version of "
            "them pursuing an alternate outcome. When the moment comes, they were simply never where you thought "
            "they were."
        ),
        "voice": (
            "Agreeable, slightly evasive, masterfully vague. Says things that mean different things to different "
            "listeners. Their clearest statements are often their most misleading. Never contradicts — redirects."
        ),
    },
}

# Merge culture preferences into ideology dicts at import time
from mechanics.culture_preferences import merge_preferences
merge_preferences(IDEOLOGIES)
