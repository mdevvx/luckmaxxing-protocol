"""Training content for the Luckmaxxing Protocol"""

# Content format: List of (speaker, message) tuples
# speaker is either "Intern" or "Gamblors"

INTRO = [
    (
        "Intern",
        "Enrolling in the Luckmaxxing program has been one of the best decisions of your life. From this moment on you are no longer an average redacted gamblor. You are now a work in progress to become a statistical anomaly.",
    ),
    ("Gamblors", "YES, CHIEF!"),
    (
        "Intern",
        "Throughout our 8 day Luckmaxxing Training we will equip you with the tools required to become one of the best. Take your training seriously, complete the exercises with focus, and you will surpass limits beyond your comprehension.",
    ),
    ("Gamblors", "YES, CHIEF!"),
    ("Intern", "Gorillions await you."),
    ("Gamblors", "GORILLIONS, CHIEF."),
]

DAY_1 = [
    (
        "Intern",
        "Your first day in the training requires a new beginning. In order for your new self to be born, your old self must die. Forget what you think you know about luck. Forget your lucky or unlucky past. Cleanse yourself of your peak net worth.",
    ),
    ("Gamblors", "Forgetting, Chief."),
    (
        "Intern",
        "Luck is a skill. By 2026 there's enough scientific evidence to prove so, and by 2033 this will become unquestionable even for normies. Research Richard Wiseman, research Dean Radin. Both are ahead of their time and now you can be too for 7 years until normies catch up.",
    ),
    ("Gamblors", "I will research chief!"),
    (
        "Intern",
        "Luck is a skill. And as such, you will learn to cultivate it. Now repeat after me: Luck is a skill!",
    ),
    ("Gamblors", "Luck is a skill!"),
    (
        "Intern",
        "Good. Cultivation begins with conviction. Mantras will be our tool to boost such conviction. Today our exercise consists in ingraining one of the most powerful luckmaxxing mantras into your being. Take 30 seconds to breathe in and out. Begin to feel your luck.",
    ),
    ("Gamblors", "Breathing!"),
    ("Intern", "Do the actual breathing, don't skip any command!"),
    ("Gamblors", "(Breathing...)"),
    (
        "Intern",
        'Good, now you are ready. Repeat calmly after me. "I am lucky. I am the luck."',
    ),
    ("Gamblors", "I am lucky. I am the luck."),
    ("Intern", "Again, harder."),
    ("Gamblors", "I AM LUCKY. I AM THE LUCK."),
    ("Intern", "Louder. Convince the universe."),
    ("Gamblors", "I AM LUCKY. I AM THE LUCK!!!"),
    (
        "Intern",
        "Good. You will now repeat this mantra daily before sunrise and before you engage in any high risk activity until it becomes a part of you. Pay close attention throughout the day, its effects won't be unnoticed.",
    ),
    ("Gamblors", "Yes sir!"),
    (
        "Intern",
        "Congratulations gamblors. Where 88% of gamblors fail and think our exercises are retarded, you pushed through and made it. You can proceed to Day 2 tomorrow.",
    ),
    ("Gamblors", "Thank you Chief!"),
]

DAY_2 = [
    (
        "Intern",
        "Welcome to Day 2, gamblor. Today we dive deeper into the mechanics of luck cultivation.",
    ),
    ("Gamblors", "Ready, Chief!"),
    # ADD YOUR DAY 2 CONTENT HERE
    # Format: ("Intern", "message") or ("Gamblors", "response")
]

DAY_3 = [
    (
        "Intern",
        "Day 3 begins now. The path to becoming a statistical anomaly continues.",
    ),
    ("Gamblors", "Let's go, Chief!"),
    # ADD YOUR DAY 3 CONTENT HERE
]

DAY_4 = [
    ("Intern", "Welcome to Day 4 of your transformation."),
    ("Gamblors", "Here, Chief!"),
    # ADD YOUR DAY 4 CONTENT HERE
]

DAY_5 = [
    ("Intern", "Day 5. You're more than halfway through your journey."),
    ("Gamblors", "Committed, Chief!"),
    # ADD YOUR DAY 5 CONTENT HERE
]

DAY_6 = [
    ("Intern", "Day 6. The advanced teachings begin now."),
    ("Gamblors", "Ready to learn, Chief!"),
    # ADD YOUR DAY 6 CONTENT HERE
]

DAY_7 = [
    ("Intern", "Day 7. You're almost there, gamblor."),
    ("Gamblors", "Pushing through, Chief!"),
    # ADD YOUR DAY 7 CONTENT HERE
]

DAY_8 = [
    (
        "Intern",
        "Day 8. The final day of your transformation into a statistical anomaly.",
    ),
    ("Gamblors", "Ready for completion, Chief!"),
    # ADD YOUR DAY 8 CONTENT HERE
]


def get_content(day):
    """
    Get content for a specific day

    Args:
        day: Day number (0 = intro, 1-8 = training days)

    Returns:
        List of (speaker, message) tuples
    """
    content_map = {
        0: INTRO,
        1: DAY_1,
        2: DAY_2,
        3: DAY_3,
        4: DAY_4,
        5: DAY_5,
        6: DAY_6,
        7: DAY_7,
        8: DAY_8,
    }
    return content_map.get(day, [])


def get_day_title(day):
    """
    Get title for a specific day

    Args:
        day: Day number (0 = intro, 1-8 = training days)

    Returns:
        Formatted title string
    """
    titles = {
        0: "🎯 Luckmaxxing Protocol - Introduction",
        1: "📅 Day 1 - The New Beginning",
        2: "📅 Day 2 - Luck Mechanics",
        3: "📅 Day 3 - Statistical Anomaly Path",
        4: "📅 Day 4 - Transformation",
        5: "📅 Day 5 - Halfway Point",
        6: "📅 Day 6 - Advanced Teachings",
        7: "📅 Day 7 - Almost There",
        8: "📅 Day 8 - Final Transformation",
    }
    return titles.get(day, f"Day {day}")
