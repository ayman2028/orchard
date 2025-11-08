Take-Home Assignment: Agent Scheduling API
==========================================

Hi there 👋

As part of the interview process for the Backend Engineer role at Orchard, we'd like you to complete a short take-home exercise. This project is designed to reflect the kind of real-world work you might do here, working with data, building APIs, and reasoning about practical backend systems.

Overview
--------

You'll be building the backend logic for a lightweight scheduling tool, something similar to Calendly or ZocDoc.

We'll provide:
-   A **SQLite database** pre-populated with agent data and existing calendar events.
-   A **reference image** showing the scheduling interface design.

Your task is to expose an API that returns all available timeslots within a given date range, based on the data provided.

You can use any programming language you're comfortable with. That said, our team is most familiar with Python and JavaScript / TypeScript, so we'll be able to review and provide feedback most effectively if you use one of those.

This project should take around 3 hours. You're encouraged to use AI tools (e.g., ChatGPT, Cursor, Copilot) for boilerplate, testing, or debugging - but you should fully understand your final solution and be able to explain it in the follow-up interview.

Requirements
------------

Functional Requirements

Create an API endpoint that returns **all available timeslots** for a given date range.
-   Input: start_date, and end_date
-   Output: JSON list of available timeslots

Constraints:
-   Appointments are **60 minutes** long.
-   Agents require a **30-minute buffer** before and after each appointment (to account for drive time).
-   Working hours: **9:00 AM - 5:00 PM**.
-   Return times in **30-minute increments**.
-   Do not schedule over existing appointments or blocked times. 
-   Agents cannot be double-booked.
-   Respect any daily or weekly appointment caps - this information is included in the database.

Assumptions:
-   The provided database is **fixed in time** -  you don't need to seed or update data.
-   All calculations can be done in a **single timezone**.
-   You don't need to implement UI components.

Deliverables
------------

When you're done, please submit the following:

1.  **Code repository** or zipped folder containing your solution.
2.  A **README** with setup instructions - explain how to install dependencies, run the project, and view results. The rest of the README content is up to you.
3.  A sample **JSON output file** containing the list of available timeslots for the start date of 6/15 and end date of 6/28.
4.  A **test suite** covering key parts of your implementation.

Expectations
------------

This project is scoped for **about 3 hours** of focused work. It's okay if you spend a bit more time polishing or debugging, but don't over-engineer it. We're evaluating how you reason, structure, and validate your solution, not how much boilerplate you can write. Clarity, correctness, and thoughtful testing matter more than perfect code.

Using AI Tools
--------------

We encourage you to use AI tools like **GitHub Copilot, Cursor, ChatGPT, or Claude (open to any others you've experimented with)** to assist you.

You might use them to:
-   Generate starter code or boilerplate
-   Suggest tests
-   Help debug or optimize your implementation

However, you should:
-   Understand everything you submit
-   Be able to explain why your code works the way it does
-   Note your use of AI tools in the README (e.g., "I used Copilot to generate initial tests and ChatGPT to check my SQL query joins.")

We'll discuss your reasoning and implementation choices during the follow-up interview.

Submission
----------

Please send your completed project (or GitHub link) to your recruiter within **72 hours** of receiving this prompt. If you need extra time for any reason, just let us know,  we're happy to accommodate.

Evaluation Focus
----------------

When we review your submission, we'll look for:
-   **Correctness**: Does it return the right timeslots?
-   **Clarity**: Is the logic easy to follow?
-   **Testing**: Are core cases validated?
-   **Reasoning**: Are trade-offs explained?
-   **AI Usage**: Did you use AI effectively and responsibly?

We're not grading you on speed or syntax, we're interested in how you think and how you structure your work.

* * * * *

### Thank You

We appreciate the time and effort you put into this.\
If anything is unclear or you hit a blocker setting up the environment, don't hesitate to reach out directly to the hiring manager.

Good luck, we're excited to see your approach!

- The Orchard Engineering Team