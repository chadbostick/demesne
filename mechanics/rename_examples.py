"""
Per-culture-option sample names for Strategy (verbs) and Make (nouns).

Used to inject contextually relevant examples into the rename prompt so the
LLM produces grounded community-practice names rather than ideology power-fantasy.

Keys are lowercase option names matching CULTURE_TREE options.
"""

RENAME_EXAMPLES: dict[str, dict[str, list[str]]] = {

    # ── Politics (orange) ──────────────────────────────────────────────────────
    "anarchy": {
        "strategies": ["Rally", "Convene", "Agitate", "Circulate", "Rouse", "Scatter", "Mobilize"],
        "makes":      ["Commons", "Open Ground", "Crossroads", "Forum", "Gather Spot", "Plaza"],
    },
    "authoritarian": {
        "strategies": ["Command", "Direct", "Conscript", "Deploy", "Assign", "Mandate", "Compel"],
        "makes":      ["Barracks", "Garrison", "Command Post", "Muster Ground", "Depot", "Armory"],
    },
    "monarchy": {
        "strategies": ["Decree", "Proclaim", "Levy", "Commission", "Appoint", "Govern", "Rule"],
        "makes":      ["Keep", "Royal Hall", "Court", "Manor", "Estate", "Throne Hall"],
    },
    "republic": {
        "strategies": ["Vote", "Propose", "Represent", "Petition", "Legislate", "Charter", "Elect"],
        "makes":      ["Council House", "Senate Hall", "Civic Hall", "Forum", "Record House", "Assembly Hall"],
    },
    "democracy": {
        "strategies": ["Ballot", "Ratify", "Amend", "Enact", "Consent", "Resolve", "Convene"],
        "makes":      ["Town Hall", "Public Square", "Ballot House", "Courthouse", "Ward House", "Open Forum"],
    },
    "empire": {
        "strategies": ["Administer", "Conscript", "Subjugate", "Expand", "Occupy", "Annex", "Govern"],
        "makes":      ["Prefecture", "Legion Hall", "Fort", "Governor's House", "Imperial Court", "Annexe"],
    },

    # ── Property (orange) ─────────────────────────────────────────────────────
    "personal": {
        "strategies": ["Claim", "Hoard", "Fence", "Guard", "Possess", "Secure", "Hold"],
        "makes":      ["Vault", "Cellar", "Lock-Up", "Cache", "Private Store", "Strongbox"],
    },
    "communal": {
        "strategies": ["Pool", "Share", "Distribute", "Steward", "Collect", "Contribute", "Portion"],
        "makes":      ["Larder", "Grain Barn", "Common Store", "Supply House", "Stockroom", "Commons Depot"],
    },
    "barter": {
        "strategies": ["Trade", "Exchange", "Swap", "Negotiate", "Broker", "Deal", "Offer"],
        "makes":      ["Trade Post", "Market Stall", "Barter Hall", "Fair Ground", "Exchange House", "Swap Meet"],
    },
    "currency": {
        "strategies": ["Price", "Mint", "Collect", "Lend", "Charge", "Budget", "Levy"],
        "makes":      ["Counting House", "Treasury", "Mint House", "Coin Hall", "Exchange", "Vault"],
    },
    "banking": {
        "strategies": ["Lend", "Credit", "Invest", "Bond", "Finance", "Underwrite", "Capitalize"],
        "makes":      ["Bank", "Lending House", "Treasury", "Reserve", "Bond House", "Credit Hall"],
    },
    "taxes": {
        "strategies": ["Levy", "Collect", "Assess", "Tithe", "Toll", "Audit", "Requisition"],
        "makes":      ["Tax House", "Tithe Barn", "Toll Gate", "Collection Office", "Revenue Hall", "Customs Post"],
    },

    # ── Spirituality (red) ────────────────────────────────────────────────────
    "ancestors": {
        "strategies": ["Remember", "Honor", "Invoke", "Commune", "Offer", "Venerate", "Mourn"],
        "makes":      ["Burial Mound", "Memory Hall", "Bone House", "Ancestor Shrine", "Reliquary", "Ossuary"],
    },
    "nature": {
        "strategies": ["Grove", "Tend", "Offer", "Observe", "Wander", "Attune", "Commune"],
        "makes":      ["Sacred Grove", "Stone Circle", "Spring Altar", "Wayshrine", "Earth Mound", "Wild Altar"],
    },
    "monotheism": {
        "strategies": ["Pray", "Preach", "Tithe", "Worship", "Sanctify", "Testify", "Observe"],
        "makes":      ["Temple", "Chapel", "Prayer Hall", "Sanctum", "Meeting House", "Holy House"],
    },
    "polytheism": {
        "strategies": ["Invoke", "Offer", "Petition", "Appease", "Sacrifice", "Dedicate", "Propitiate"],
        "makes":      ["Shrine Row", "Idol House", "Offering Court", "Votive House", "Temple Court", "Sacred Hall"],
    },
    "science": {
        "strategies": ["Study", "Observe", "Test", "Record", "Question", "Probe", "Measure"],
        "makes":      ["Academy", "Observatory", "Library", "Record House", "Study Hall", "Archive"],
    },
    "mysticism": {
        "strategies": ["Meditate", "Divine", "Seek", "Contemplate", "Fast", "Retreat", "Intuit"],
        "makes":      ["Sanctum", "Hermitage", "Retreat", "Oracle House", "Vision House", "Inner Chamber"],
    },

    # ── Mindset (blue) ────────────────────────────────────────────────────────
    "impulsive": {
        "strategies": ["Speak Out", "React", "Voice", "Cry Out", "Announce", "Declare", "Call Out"],
        "makes":      ["Open Floor", "Rally Point", "Gather Green", "Speak Corner", "Call House", "Impulse Court"],
    },
    "cautious": {
        "strategies": ["Weigh", "Consider", "Deliberate", "Assess", "Review", "Examine", "Consult"],
        "makes":      ["Council Room", "Quiet Hall", "Counsel Chamber", "Review Room", "Think House", "Deliberation Hall"],
    },
    "rational": {
        "strategies": ["Reason", "Argue", "Analyze", "Deduce", "Prove", "Infer", "Compare"],
        "makes":      ["Debate Hall", "Argument House", "Reason Hall", "Logic Room", "Inquiry Room", "Proof Hall"],
    },
    "emotional": {
        "strategies": ["Share", "Grieve", "Express", "Witness", "Confide", "Comfort", "Encourage"],
        "makes":      ["Healing House", "Story Circle", "Comfort Hall", "Open Hall", "Witness Hall", "Circle Room"],
    },
    "diplomatic": {
        "strategies": ["Mediate", "Negotiate", "Broker", "Reconcile", "Arbitrate", "Accord", "Bridge"],
        "makes":      ["Peace Hall", "Treaty House", "Accord House", "Neutral Ground", "Mediation Room", "Meeting House"],
    },
    "isolationist": {
        "strategies": ["Convene", "Settle", "Resolve", "Conclude", "Determine", "Affirm", "Decide"],
        "makes":      ["Inner Hall", "Closed Council", "Private Forum", "Sealed Chamber", "Ward Hall", "Kin Hall"],
    },

    # ── Social Order (blue) ───────────────────────────────────────────────────
    "fraternal": {
        "strategies": ["Apprentice", "Mentor", "Confer", "Weigh", "Compare", "Deliberate", "Experiment", "Practice"],
        "makes":      ["Lodge", "Dormitory", "Public House", "Guildhall", "Headquarters", "Market", "Venue"],
    },
    "familial": {
        "strategies": ["Gather", "Bond", "Counsel", "Settle", "Advise", "Pass Down", "Teach", "Remember"],
        "makes":      ["Hearth Hall", "Kin Hall", "Clan House", "Ancestral Home", "Family House", "Home Hall"],
    },
    "tribal": {
        "strategies": ["Council", "Speak", "Witness", "Honor", "Challenge", "Claim", "Assert", "Declare"],
        "makes":      ["Longhouse", "Council Fire", "Tribal Hall", "Moot", "Chief's Hall", "Meeting Ground"],
    },
    "hierarchical": {
        "strategies": ["Report", "Defer", "Appoint", "Advance", "Discipline", "Assign", "Rank", "Elevate"],
        "makes":      ["Audience Chamber", "Hall of Rank", "Status House", "Order Hall", "Protocol Room", "Rank House"],
    },
    "class": {
        "strategies": ["Assert", "Maintain", "Enforce", "Rise", "Claim", "Establish", "Demand", "Prove"],
        "makes":      ["Merchant's Quarter", "Station House", "Status Hall", "Privilege House", "Noble Court", "Estate Hall"],
    },
    "meritocracy": {
        "strategies": ["Excel", "Compete", "Demonstrate", "Earn", "Qualify", "Advance", "Distinguish", "Prove"],
        "makes":      ["Proving Ground", "Trial Hall", "Merit Hall", "Achievement House", "Competition Hall", "Test Ground"],
    },

    # ── Values (green) ────────────────────────────────────────────────────────
    "strength": {
        "strategies": ["Train", "Challenge", "Forge", "Harden", "Test", "Discipline", "Prove", "Push"],
        "makes":      ["Training Ground", "Sparring Yard", "Proving Ground", "Challenge Field", "Stronghold", "Muster Ground"],
    },
    "knowledge": {
        "strategies": ["Teach", "Learn", "Study", "Archive", "Question", "Seek", "Illuminate", "Guide"],
        "makes":      ["Library", "School House", "Lore Hall", "Study Hall", "Teaching Hall", "Archive Hall"],
    },
    "talent": {
        "strategies": ["Discover", "Cultivate", "Nurture", "Display", "Recognize", "Develop", "Exhibit", "Reveal"],
        "makes":      ["Talent Hall", "Showcase", "Exhibition House", "Discovery House", "Display Hall", "Studio"],
    },
    "skill": {
        "strategies": ["Practice", "Master", "Refine", "Demonstrate", "Hone", "Craft", "Perfect", "Teach"],
        "makes":      ["Workshop", "Craft Hall", "Practice Hall", "Guild House", "Master's House", "Skill Hall"],
    },
    "prestige": {
        "strategies": ["Honor", "Celebrate", "Commemorate", "Proclaim", "Elevate", "Acclaim", "Distinguish", "Recognize"],
        "makes":      ["Monument", "Hall of Honor", "Glory Hall", "Fame House", "Memorial Hall", "Trophy House"],
    },
    "power": {
        "strategies": ["Command", "Assert", "Seize", "Dominate", "Direct", "Control", "Lead", "Rule"],
        "makes":      ["Seat of Power", "Command Hall", "Authority House", "Throne Room", "Center Hall", "Power Hall"],
    },

    # ── Production (pink) ─────────────────────────────────────────────────────
    "farming": {
        "strategies": ["Plant", "Tend", "Harvest", "Sow", "Cultivate", "Reap", "Till", "Grow"],
        "makes":      ["Farmstead", "Granary", "Barn", "Field House", "Harvest Hall", "Tilling Yard"],
    },
    "hunting": {
        "strategies": ["Track", "Hunt", "Stalk", "Scout", "Pursue", "Trap", "Flush", "Range"],
        "makes":      ["Hunting Lodge", "Game House", "Trap Yard", "Track Hall", "Range House", "Hunter's Post"],
    },
    "raiding": {
        "strategies": ["Raid", "Strike", "Pillage", "Plunder", "Ambush", "Seize", "Press", "Take"],
        "makes":      ["War Camp", "Raiding Post", "Plunder House", "Strike Base", "Ambush Ground", "War Lodge"],
    },
    "trading": {
        "strategies": ["Trade", "Peddle", "Carry", "Transport", "Deal", "Move", "Haul", "Exchange"],
        "makes":      ["Trading Post", "Market Hall", "Caravan House", "Way Station", "Commerce Hall", "Transport Yard"],
    },
    "manufacturing": {
        "strategies": ["Forge", "Produce", "Process", "Fabricate", "Smelt", "Build", "Construct", "Manufacture"],
        "makes":      ["Forge", "Works", "Smithy", "Factory Hall", "Processing Yard", "Production House"],
    },
    "mining": {
        "strategies": ["Dig", "Extract", "Delve", "Mine", "Prospect", "Bore", "Quarry", "Excavate"],
        "makes":      ["Mine Shaft", "Quarry Hall", "Ore House", "Prospect Hall", "Dig Site", "Smelter"],
    },

    # ── Natural Affinity (pink) ───────────────────────────────────────────────
    "earth": {
        "strategies": ["Dig", "Root", "Cultivate", "Ground", "Till", "Burrow", "Settle", "Anchor"],
        "makes":      ["Stone House", "Root Yard", "Soil Works", "Earth Hall", "Dig Ground", "Stone Yard"],
    },
    "water": {
        "strategies": ["Flow", "Draw", "Fish", "Dive", "Sail", "Navigate", "Channel", "Collect"],
        "makes":      ["Cistern", "Fish House", "River Post", "Dock Yard", "Water Hall", "Basin"],
    },
    "air": {
        "strategies": ["Scout", "Scan", "Listen", "Signal", "Carry", "Glide", "Drift", "Range"],
        "makes":      ["Watch Tower", "Signal Post", "Lookout", "Wind House", "Aerie", "Signal Fire"],
    },
    "fire": {
        "strategies": ["Burn", "Forge", "Kindle", "Light", "Smelt", "Purge", "Temper", "Ignite"],
        "makes":      ["Forge", "Fire Pit", "Kiln", "Hearth Hall", "Smelter", "Char House"],
    },
    "light": {
        "strategies": ["Illuminate", "Reveal", "Guide", "Beacon", "Mark", "Signal", "Show", "Shine"],
        "makes":      ["Beacon", "Light House", "Signal Tower", "Lantern Hall", "Guide Post", "Shine Hall"],
    },
    "dark": {
        "strategies": ["Conceal", "Hide", "Shadow", "Lurk", "Mask", "Veil", "Obscure", "Watch"],
        "makes":      ["Safe House", "Hidden Hall", "Vault", "Shadow Post", "Cover House", "Dark Hall"],
    },
}
