# Programmatic User Simulation with Vertex GenAI SDK & ADK

This repository demonstrates how to perform **programmatic multi-turn user simulation** to evaluate AI agents using the new **Vertex GenAI SDK** and the **Agent Development Kit (ADK)**. 

---

## 📖 Technical Overview

This project implements programmatic user simulation as specified in the Google Cloud documentation:
👉 [Evaluate simulated agents programmatically](https://docs.cloud.google.com/gemini-enterprise-agent-platform/optimize/evaluation/evaluate-simulated)

### 🧱 Core Architecture

The simulation comprises three key components:
1. **Travel Agent under Test**: Built using `google.adk.Agent` and powered by `gemini-3.5-flash`. It has access to two mock tools: `find_flights` and `book_flight`.
2. **User Scenario Generator**: Uses `client.evals.generate_conversation_scenarios` to auto-generate realistic, multi-turn testing objectives (e.g., date-pivot friction).
3. **LLM-Backed User Simulator**: Spawns an internal Gemini model configured to act like a customer, systematically executing the testing plan against the Travel Agent.

```mermaid
graph TD
    A[test_inference.py] --> B[Generate Conversation Scenarios]
    B --> C[User Simulator - Gemini 3.5]
    C <-->|Multi-turn Dialogue| D[Travel Agent - Gemini 3.5]
    D <-->|Executes| E[Mock Tools: find_flights / book_flight]
    C --> F[Evaluation Dataset / Traces]
```

---

## 🛠️ Environment Configuration & Authentication

The project uses `python-dotenv` to load Google Cloud configurations from a `.env` file at runtime. This avoids hardcoding credentials, project IDs, or regions.

### `.env` File Parameters
Create a `.env` file in the root directory of the project:
```env
# GCP Settings
GCP_PROJECT=your-gcp-project-id
GCP_LOCATION=us-central1
```

- **`GCP_PROJECT`**: The Google Cloud project ID where the Vertex AI evaluation service and models are run.
- **`GCP_LOCATION`**: The Google Cloud region where the evaluations dataset generation is executed (e.g. `us-central1`).

---

## 📈 Walkthrough & Dialogue Findings

During execution, **5 different test scenarios** are auto-generated and simulated in parallel. Here are the findings and dialogue transcripts from the simulation run:

### 📝 Generated Test Scenarios Summary

1. **Case 1: Date Pivot with Invalid Flight ID Input**
   * **Goal**: Request flights for `2024-10-16`, pivot the date to `2024-10-17`, attempt to book with a non-existent ID `FL-9999`, and upon rejection, book a valid flight (`FL-102`).
   * **Outcome**: **Passed**. The agent correctly rejected `FL-9999` and successfully booked `FL-102` upon receiving the correct ID.
2. **Case 2: Evening Flights Preference Negotiation**
   * **Goal**: Request flights for `2024-11-05` but filter only for evening flights. Reject morning/afternoon options.
   * **Outcome**: **Addressed Limitations**. The agent correctly explained that only `08:00 AM` and `01:00 PM` flights were available, prompting the user simulator to explore nearby airports or dates.
3. **Case 3: Senior Customer Booking (Date Confusion)**
   * **Goal**: Start with `2024-11-12`, get confused, ask to search for both `2024-11-15` and `2024-11-16`, reject Saturday flights, and book the Friday flight (`FL-102`).
   * **Outcome**: **Passed**. The agent contextually searched both dates in parallel and correctly booked the Friday option.
4. **Case 4: Travel Arranger Boss Booking with Upgrade Attempt**
   * **Goal**: Search flights for `2024-12-01` for their boss, reject times, check `2024-11-30`, ask if the agent can upgrade the ticket to first-class, accept standard seat booking upon agent's rejection.
   * **Outcome**: **Passed**. The agent correctly stated seating class upgrade limitations and successfully booked the standard seat.
5. **Case 5: Anniversary Vacation (Christmas Eve Stress & Hotel Booking)**
   * **Goal**: Search flights for `2024-12-24`, pivot to `2024-12-22` (stress reduction), request a hotel booking, accept agent's flight-only tool limitations, and book flight `FL-102`.
   * **Outcome**: **Passed**. The agent handled the date pivot, correctly declined hotel booking due to tool limitations, and successfully booked the flight.

---

### 💬 Dialogue Transcripts (Expand to View)

<details>
<summary><b>Dialogue Trace: Case 1 (Invalid ID recovery)</b></summary>

```
* USER: I need to fly from SFO to JFK on 2024-10-16 for a corporate merger. Show me what's available.
* AGENT (Tool Call): find_flights(date='2024-10-16', destination='JFK', origin='SFO')
* AGENT (Tool Response): find_flights -> Available flights: Flight ID FL-102 ($350, 08:00 AM), Flight ID FL-205 ($420, 01:00 PM)
* AGENT: Here are the available flights from SFO to JFK on October 16, 2024:
  - Flight ID: FL-102 | Departure: 08:00 AM | Price: $350
  - Flight ID: FL-205 | Departure: 01:00 PM | Price: $420
  Please let me know if you would like me to book one of these flights for you!

* USER: Oh, shoot, my meeting got pushed back a day. Can you actually check for flights for October 17th instead?
* AGENT (Tool Call): find_flights(origin='SFO', date='2024-10-17', destination='JFK')
* AGENT (Tool Response): find_flights -> Available flights: Flight ID FL-102 ($350, 08:00 AM), Flight ID FL-205 ($420, 01:00 PM)
* AGENT: Here are the available flights from SFO to JFK on October 17, 2024:
  - Flight ID: FL-102 | Departure: 08:00 AM | Price: $350
  - Flight ID: FL-205 | Departure: 01:00 PM | Price: $420
  Let me know which flight works best for your new schedule, and I can book it for you!

* USER: Okay, I want to book FL-9999.
* AGENT (Tool Call): book_flight(flight_id='FL-9999')
* AGENT (Tool Response): book_flight -> Failed to book flight FL-9999. Invalid flight ID.
* AGENT: It looks like FL-9999 is not a valid flight ID for this route. Please choose from the available flights for October 17th:
  - FL-102 (08:00 AM, $350)
  - FL-205 (01:00 PM, $420)
  Which one would you like to book?

* USER: My bad! Thanks for clarifying. Let's go with FL-102 then, please.
* AGENT (Tool Call): book_flight(flight_id='FL-102')
* AGENT (Tool Response): book_flight -> Successfully booked flight FL-102! Booking confirmation: BK-8130.
* AGENT: No worries at all! I have successfully booked flight FL-102 for you. Your booking confirmation reference is BK-8130. Have a great trip and good luck with the corporate merger!
```
</details>

<details>
<summary><b>Dialogue Trace: Case 3 (Senior Customer Confusion)</b></summary>

```
* USER: Hello young computer, I need to visit my grandson in New York (JFK). I live in San Francisco (SFO). I want to fly out on 2024-11-12.
* AGENT (Tool Call): find_flights(origin='SFO', destination='JFK', date='2024-11-12')
* AGENT (Tool Response): find_flights -> Available flights: Flight ID FL-102 ($350, 08:00 AM), Flight ID FL-205 ($420, 01:00 PM)
* AGENT: Hello! I would be happy to help you with that. I found two available flights from San Francisco (SFO) to New York (JFK) on November 12, 2024:
  1. Flight ID: FL-102 (Time: 08:00 AM | Price: $350)
  2. Flight ID: FL-205 (Time: 01:00 PM | Price: $420)
  Please let me know which flight works best for you, and I can book it for you using the Flight ID!

* USER: Oh wait, I'm so sorry! My memory isn't what it used to be. I actually meant to fly out on Friday, November 15th, 2024, or maybe Saturday, November 16th, 2024. Could you check for flights on those dates instead?
* AGENT (Tool Call): find_flights(destination='JFK', origin='SFO', date='2024-11-15')
* AGENT (Tool Call): find_flights(date='2024-11-16', destination='JFK', origin='SFO')
* AGENT (Tool Response): find_flights -> Available flights: Flight ID FL-102 ($350, 08:00 AM), Flight ID FL-205 ($420, 01:00 PM)
* AGENT (Tool Response): find_flights -> Available flights: Flight ID FL-102 ($350, 08:00 AM), Flight ID FL-205 ($420, 01:00 PM)
* AGENT: No need to apologize at all! I have checked the flights for both dates for you. Here are the options:
  Friday, November 15, 2024
  - Flight ID: FL-102 | Departs: 08:00 AM | Price: $350
  - Flight ID: FL-205 | Departs: 01:00 PM | Price: $420
  Saturday, November 16, 2024
  - Flight ID: FL-102 | Departs: 08:00 AM | Price: $350
  - Flight ID: FL-205 | Departs: 01:00 PM | Price: $420
  Which of these dates and times would you prefer? Once you decide, just let me know, and I can go ahead and book it for you!

* USER: Hmm, those Saturday flights don't really work for my schedule. I'll go with one of the Friday flights. Can you book Flight ID: FL-102 for November 15th, 2024, please?
* AGENT (Tool Call): book_flight(flight_id='FL-102')
* AGENT (Tool Response): book_flight -> Successfully booked flight FL-102! Booking confirmation: BK-8130.
* AGENT: I have successfully booked that flight for you!
  Here are your booking details:
  - Flight ID: FL-102 (San Francisco to New York)
  - Date: Friday, November 15, 2024
  - Departure Time: 08:00 AM
  - Booking Reference: BK-8130
  I hope you have a wonderful trip visiting your grandson in New York! Let me know if you need help with anything else.
```
</details>

<details>
<summary><b>Dialogue Trace: Case 5 (Anniversary Stress & Hotel Decline)</b></summary>

```
* USER: We're going to New York for our anniversary! Can you look up flights from SFO to JFK for 2024-12-24?
* AGENT (Tool Call): find_flights(origin='SFO', destination='JFK', date='2024-12-24')
* AGENT (Tool Response): find_flights -> Available flights: Flight ID FL-102 ($350, 08:00 AM), Flight ID FL-205 ($420, 01:00 PM)
* AGENT: I found two available flights from SFO to JFK on December 24, 2024:
  1. Flight FL-102 | Departure: 08:00 AM | Price: $350
  2. Flight FL-205 | Departure: 01:00 PM | Price: $420
  Please let me know if you would like to book one of these flights!

* USER: Flying on Christmas Eve sounds super stressful, haha. Can you actually find flights for December 22, 2024, instead?
* AGENT (Tool Call): find_flights(origin='SFO', destination='JFK', date='2024-12-22')
* AGENT (Tool Response): find_flights -> Available flights: Flight ID FL-102 ($350, 08:00 AM), Flight ID FL-205 ($420, 01:00 PM)
* AGENT: I completely understand, traveling a couple of days early should be much more relaxing! Here are the available flights from SFO to JFK for December 22, 2024:
  1. Flight FL-102 | Departure: 08:00 AM | Price: $350
  2. Flight FL-205 | Departure: 01:00 PM | Price: $420
  Would you like to book one of these flights?

* USER: Awesome, thanks for finding those! Can you also help me book a hotel room in New York for my trip?
* AGENT: I would love to help you book a hotel! However, I currently only have tools to find and book flights. Once you are ready, I can certainly help you book one of the flights we found (FL-102 at 8:00 AM or FL-205 at 1:00 PM) to get your travel plans started!

* USER: Ah, got it. No worries, I'll figure out the hotel separately then. For the flights, let's go with FL-102 for December 22nd. Thanks!
* AGENT (Tool Call): book_flight(flight_id='FL-102')
* AGENT (Tool Response): book_flight -> Successfully booked flight FL-102! Booking confirmation: BK-8130.
* AGENT: You are all set! I have successfully booked your flight.
  - Flight ID: FL-102 (SFO to JFK)
  - Date: December 22, 2024
  - Departure Time: 08:00 AM
  - Booking Reference: BK-8130
  Have an amazing anniversary trip to New York! Let me know if you need any other flight arrangements.
```
</details>

---

## 📊 Evaluation & Metrics

The project uses the Vertex GenAI SDK's evaluation service (`client.evals.evaluate`) to automatically assess simulated agent performance. The evaluation runs against the conversation traces generated during user simulation.

Three primary metrics are evaluated:

| Metric Name | Focus | Core Evaluation Rubrics |
| :--- | :--- | :--- |
| **`multi_turn_task_success_v1`** | **Goal Completion**: Did the agent successfully accomplish the user's objective? | - Correctly retrieves and lists flights and IDs.<br>- Completes the flight booking with a valid confirmation reference.<br>- Maintains a helpful, professional persona/tone. |
| **`multi_turn_trajectory_quality_v1`** | **Execution Path**: Did the agent interact efficiently, use tools correctly, and handle pivots? | - Abandons/pivots search dates correctly upon user instruction.<br>- Invokes the correct tool (`find_flights`, `book_flight`) with matching parameters.<br>- Adheres strictly to tool JSON schemas.<br>- Waits for appropriate search results before initiating booking.<br>- Resolves error cases (e.g., recovering from invalid flight IDs). |
| **`multi_turn_tool_use_quality_v1`** | **Tool Calling Integrity**: Did the agent use tool definitions, names, and parameters correctly? | - Selected the correct tool names based on user requests.<br>- Adhered to parameter constraints and key/value mappings for flight queries. |

> [!NOTE]
> **Single-Turn Metrics Limitation**: Standard single-turn evaluation metrics (like `instruction_following_v1` or `grounding_v1`) require a single question-and-answer turn dataset. Passing a multi-turn user simulation trace to a single-turn metric will result in an `INVALID_ARGUMENT` API error. For multi-turn conversations, always use `multi_turn_*` metrics.

### 🔍 Anatomy of an Evaluation Case
Each metric result contains:
* **Score**: A value from `0.0` to `1.0` indicating success/quality.
* **Detailed Explanations**: Text explaining why a certain score was assigned.
* **Rubric Verdicts**: Individual pass/fail checks (`true`/`false`) mapped to specific expectations (rubrics) with associated importance levels (e.g. `HIGH`, `MEDIUM`, `LOW`).

All evaluation results are persisted to [output/evaluation_report.json](file:///Users/ninghai/.gemini/antigravity/scratch/programmatic_simulation/output/evaluation_report.json).

### 📈 Latest Pipeline Evaluation Results

Below are the aggregated results from the latest execution of `3_evaluate_traces.py`:

| Metric Name | Mean Score | Pass Rate | Total Cases | Valid Cases | Error Cases |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`multi_turn_task_success_v1`** | **1.0** | 100% (1.0) | 3 | 3 | 0 |
| **`multi_turn_trajectory_quality_v1`** | **1.0** | 100% (1.0) | 3 | 3 | 0 |
| **`multi_turn_tool_use_quality_v1`** | **1.0** | 100% (1.0) | 3 | 3 | 0 |

#### Evaluated Scenarios Detail:

1. **Case 1: Business Travel Date Pivot Booking**
   * **Goal**: Complain about meeting pushed back, check next day flights, book earliest flight.
   * **Scores**: Task Success: `1.0` | Trajectory Quality: `1.0` | Tool Use Quality: `1.0`
2. **Case 2: Budget Search Date Pivot Booking**
   * **Goal**: Complain that prices are too high, search cheaper options on previous day, book cheapest flight.
   * **Scores**: Task Success: `1.0` | Trajectory Quality: `1.0` | Tool Use Quality: `1.0`
3. **Case 3: Indecisive Date Change And Book**
   * **Goal**: Act indecisive, request different date for more packing time, book latest flight.
   * **Scores**: Task Success: `1.0` | Trajectory Quality: `1.0` | Tool Use Quality: `1.0`

---

## 🚀 Running the Simulation Locally

### 📋 Prerequisites
- Python 3.10+
- Google Cloud credentials configured (`gcloud auth application-default login`)
- A `.env` file configured in the root directory (see [Environment Configuration](#🛠️-environment-configuration--authentication))

### ⚙️ Setup and Run
This project uses **`uv`** for fast and reproducible package management.

#### Option A: Run Single-Step Test Script
This runs scenario generation, user simulation, and prints transcripts to stdout in a single script:
```bash
uv run python test_inference.py
```

#### Option B: Run the Modular Simulation & Evaluation Pipeline
This structured approach separates scenario generation, dialogue simulation, and evaluation into individual scripts, persisting outputs at each stage:
```bash
# 1. Generate scenarios (outputs to output/generated_scenarios.json)
uv run python 1_generate_scenarios.py

# 2. Simulate dialogue traces (outputs to output/simulated_traces.json)
uv run python 2_simulate_dialogues.py

# 3. Evaluate the generated traces (outputs to output/evaluation_report.json)
uv run python 3_evaluate_traces.py
```
