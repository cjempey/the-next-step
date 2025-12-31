# MVP Requirements Document: What Next?

AI-assisted task suggestion service for neurodivergent individuals to move from uncertainty to action.

---

## 1. Product Overview

### 1.1 Purpose

Support neurodivergent adults (primarily autistic and ADHD individuals) in **executing tasks aligned with personal values**, reducing decision paralysis, and maintaining momentum without coercion, judgment, or gamification.

### 1.2 Primary Users

- Neurodivergent individuals (ADHD, autism, or combination)
- Personal life context (home, health, self-improvement)
- Solo user initially; multi-user sharing deferred to v2

### 1.3 Primary Outcome

- **Completed tasks** (proxy for reduced overwhelm)
- **Consistent engagement** with the system
- **Agency preserved** at all times (user is final arbiter)

### 1.4 Non-Goals

- Behavior modification or coercion
- Productivity optimization or performance metrics
- Gamification (streaks, points, rankings)
- Time tracking or duration estimation

### 1.5 Context

- Personal life context (not work/team-based)
- Mobile-first with optional web interface
- Low cognitive load, suitable for interruptions and limited working memory
- Offline-capable (sync deferred to v2)

---

## 2. Design Principles

1. **Agency First:** Users decide what to do; system only suggests.
2. **Neutral Language:** No moralizing, ranking, "should," or judgment.
3. **Low-Friction Interaction:** Single-task suggestions, minimal decisions.
4. **Transparency:** Users see why tasks are suggested (scoring rationale visible during planning).
5. **Interruptibility:** All flows can be paused or deferred without consequence.
6. **Data Visibility:** Users retain full control over task state, history, and notes.
7. **Respect Unknown Energy:** System cannot know user's motivation/energy; fuzziness prevents nagging same task.

---

## 3. Task Model

### 3.1 Task Attributes

- **Title:** Short phrase (e.g., "Water the plants")
- **Value(s):** Link to one or more user-defined values
- **Impact:** A, B, C, or D (user-assigned, with AI suggestions)
- **Urgency:** 1–4 (user-assigned, with AI suggestions)
- **Due Date:** Optional date when task should be completed
- **Recurrence:** None, daily, weekly, or custom pattern
- **State:** Ready, In Progress, Blocked, Parked, Completed, or Cancelled
- **Notes:** Optional reflective text (captured during review, not processed by system)
- **Completion %:** Optional metadata for partial progress (captured during review)

### 3.2 Task States & Transitions

| State | Meaning | Allowed Transitions | Notes |
|-------|---------|-------------------|-------|
| **Ready** | Ready to start | → In Progress | Default for new tasks; included in suggestions |
| **In Progress** | Currently working on | → Completed, Blocked, Parked | Multiple allowed concurrently |
| **Blocked** | Can't proceed; waiting on external factor | → Ready, Parked, Cancelled | Excluded from suggestions |
| **Parked** | Intentionally deferred without penalty | → Ready, Cancelled | Excluded from suggestions |
| **Completed** | Done | — | Final state; recurring tasks auto-create next instance |
| **Cancelled** | Not doing this anymore | — | Final state; no auto-reactivation |

### 3.3 Task Size

- Defined as "something you can accomplish in one go"
- System does not enforce task breakdown (user can request AI assistance via review card)
- Recurring tasks supported (daily, weekly, custom patterns)

### 3.4 Recurring Tasks

- When a recurring task completes, the next instance is **automatically created** with the same attributes
- New instance placed in Ready state
- A card appears in next review session: "Next instance of [Task] created for tomorrow"

---

## 4. Values System

### 4.1 Value Definition

- Users define **short value statements** (e.g., "I am improving in my craft," "My family comes first")
- No hard limits on number of values
- Clarity improves task suggestion accuracy
- Example: User might have 3-5 core values

### 4.2 Value Usage

- Tasks link to one or more values
- During evening review, metrics are shown per value: "You completed 3 tasks aligned with [Value]"
- Values provide context for task impact assessment

### 4.3 Value Lifecycle

- Values can be archived/deactivated
- Archived values do not affect existing task-value links
- Tasks linked to archived values are not automatically changed
- User can manually update task-value links if needed

---

## 5. Impact & Urgency

### 5.1 Impact Categories

- **A:** Directly advance values/goals
- **B:** Moderately aligned with values
- **C:** Minor alignment
- **D:** Little or no impact on values

AI may suggest impact based on task title and linked values; user retains final authority.

### 5.2 Urgency Categories

- **1:** Immediate due; high penalty if delayed (e.g., bill due today)
- **2:** Due soon (e.g., within next few days)
- **3:** Can be deferred (e.g., next week)
- **4:** Long-term or optional (e.g., nice-to-have)

AI may suggest urgency based on due date and task description; user retains final authority.

### 5.3 Strategic Nudge

- Tasks that are A-impact but low-urgency (A3/A4) receive a **probabilistic boost** during suggestion
- Prevents urgency bias from completely drowning out important-but-not-urgent work
- Boost is subtle and non-deterministic; never forces selection

---

## 6. MVP Core Flows

### 6.1 Task Entry

**Triggers:** User selects "Create Task" or "Add Task"

**Process:**
1. User enters task title
2. System prompts for: Value(s), impact (with AI suggestion), Urgency (with AI suggestion), Due date (optional), Recurrence (optional)
3. User saves task
4. Task created in Ready state

**Notes:**
- AI suggestions should be non-blocking (user can accept/override)
- Values must exist before task creation (values entry prerequisite)

---

### 6.2 Values Entry

**Triggers:** User selects "Define Values" or during first-run setup

**Process:**
1. User enters a value statement (short phrase or sentence)
2. System saves value
3. Value available for linking to tasks

**Notes:**
- Values can be edited or archived at any time
- No enforced limit on number of values

---

### 6.3 Morning Planning

**Triggers:** User initiates manually OR system prompts at user-configurable time

**Purpose:** User selects priority tasks for the day + reviews carryovers/blocked/upcoming tasks

**Process:**

1. **Section 1: "From Yesterday's Review"**
   - In-Progress carryovers (with completion % and notes if captured)
   - "Break down" tasks created during review
   - Prompt: "Did you want to continue these or adjust them?"

2. **Section 2: "Ready or Unblocked"**
   - Tasks currently in Blocked or Parked state
   - Grouped separately
   - Prompt: "Any of these ready to tackle now?"
   - User can move back to Ready state if willing to try

3. **Section 3: "Upcoming Due Dates"**
   - All tasks with due date within next 7 days
   - If >3 tasks with due dates exist, show top 3 by weighted score
   - Ranked by score (descending)
   - Prompt: "These have due dates coming up—want to prioritize any?"

4. **Section 4: "Other Ready Tasks"**
   - Remaining Ready tasks not shown above
   - Ranked by weighted score (descending)
   - Scrollable; user can browse and add to priorities if desired

**Selection Interface:**
- **Web:** Two-column drag-and-drop (all tasks left, "Today's Priorities" column right)
- **Mobile:** Single column with checkboxes to add to "Today's Priorities"

**Score Transparency:**
- Scores displayed as ranked list, not numeric values
- Tooltip/expandable shows scoring breakdown:
  - "Why is this ranked here?"
  - Input factors: impact, Urgency, Due date proximity, Recurrence, Strategic nudge status
  - Human-readable explanation (e.g., "A-impact + due in 2 days")
- Goal: Transparency into system reasoning without gamification

**Selection Constraints:**
- No enforced limit on number of priorities (but UI can suggest "5-7 is realistic")
- Selection is purely additive; doesn't prevent other tasks from appearing in "what next"

**Outcome:**
- User saves "Today's Priorities" list
- Selected tasks receive +multiplier (boost) to their suggestion weight for the day
- Boost expires at evening review (must re-select tomorrow if still a priority)

**Important:** If user skips morning planning, the system still functions—"what next" suggestions proceed using the full weighted algorithm without day-specific boost.

---

### 6.4 "What Next?" Flow (Single Candidate Version)

**Triggers:** User selects "What Next?" or receives a notification prompt

**Purpose:** Reduce cognitive burden by suggesting exactly one task, with option to accept, defer, or take a break

**Process:**

1. **Check In-Progress Tasks**
   - If user has In-Progress tasks, present them first
   - Prompt: "You were working on X. Continue with that, or would you like a different suggestion?"
   - Options: "Continue this" or "Suggest something else"

2. **Generate Candidate Pool**
   - Include: All Ready tasks + optionally In-Progress tasks (for context)
   - Exclude: Completed, Blocked, Parked, Cancelled
   - Apply weighting factors:
     - **Base Score** = (impact × weight_i) + (Urgency × weight_u) + (Strategic Nudge × weight_s)
     - **Daily Priority Boost** = +multiplier if task in "Today's Priorities" (or +1.0x if not)
     - **Rejection Dampening** = ÷ dampening_factor if rejected in current session
   - Normalize scores to probabilities (roulette wheel distribution, not deterministic max)

3. **Select Candidate**
   - Randomly select one task using weighted probabilities
   - Result: Exactly one suggestion

4. **Present Candidate**
   - Neutral framing: "How about working on [Task Name]?"
   - Show: Task title, linked values, impact/urgency
   - Options: "I'll start this now" / "Not now, suggest another" / "I'll take a break"

5. **User Responses**

   **"I'll start this now":**
   - Move task to In Progress state
   - Confirm: "Okay, let's go. I'll check in with you later."
   - Clear rejection dampening for this session
   - End flow

   **"Not now, suggest another":**
   - Apply rejection dampening to this task (reduce weight by factor, e.g., 50%)
   - Dampening scope: Lasts until **next Break action** OR **next Evening Review** (whichever first)
   - Select new candidate (excluding dampened task, or with greatly reduced probability)
   - Present new suggestion
   - User can repeat this until they find a task they'll start

   **"I'll take a break":**
   - End flow immediately
   - **Clear all rejection dampening** for this session
   - Do not change any task states
   - No automatic suggestion until user requests "what next" again
   - Resets the dampening session boundary

**Tone:** Neutral, supportive, never coercive. No "should," no ranking language.

**Mobile-Specific:**
- Low-bandwidth interface; single candidate per notification
- Buttons large and touch-friendly
- Optional notification support (push alerts for suggestions)

---

### 6.5 "What Was I Doing?" (Context Recovery)

**Triggers:** User selects "What was I doing?" or system prompts on app open (mobile) / session start (web)

**Purpose:** Remind user of In-Progress tasks without judgment

**Process:**

1. Query all tasks in In-Progress state
2. Display as simple list: Task name, linked values, any notes from last review
3. Buttons: "Continue with [Task]" or "Go to morning planning" or "Ask me later"

**Notes:**
- No state changes made by viewing this flow
- Purely informational; helps user context-switch back to what they were doing
- Mobile can auto-prompt on app open; web can show as sidebar or optional panel

---

### 6.6 Evening Review

**Triggers:** User initiates manually OR system prompts at user-configurable time (e.g., 6 PM)

**Purpose:** Reflect on day, capture partial progress, and generate system cards for next morning

**Process:**

System generates applicable **review cards** based on day's activity. Each card is modular with its own response options.

#### **Card Type 1: Completion Summary** (Always appears)

**Content:** "You completed N tasks today" + list of completed tasks (grouped by value if helpful)

**Responses:** Acknowledge/dismiss (informational)

**Actions:** None

---

#### **Card Type 2: Task Rejection/Skip** (Appears if task rejected ≥3 times in a day)

**Content:** "You skipped [Task Name] 3 times today. What can we do to help?"

**Response Options:**
1. "Help break it down"
2. "Maybe later" (reflective, no action)
3. "Not relevant anymore"

**Actions:**
1. "Help break it down"
   - Create new task: "Break down: [Task Name]"
   - Place in Ready state
   - Tag as [Breakdown Task] for visibility
   - User will see this during morning planning next day
   - Separate AI conversation flow deferred to v2; focus is on capturing intent now

2. "Maybe later"
   - Log reflection (no system action)
   - Task state unchanged
   - User note: Purely for user's own reflection next day

3. "Not relevant anymore"
   - Move task to Cancelled state
   - Final state; no reactivation

---

#### **Card Type 3: In-Progress Task** (Appears for each task in In-Progress state at review start)

**Content:** "You were working on [Task Name]. What's the status?"

**Response Options:**
1. "Completed"
2. "Continue tomorrow"
3. "Block it"
4. "Park it"

**Actions:**
1. "Completed"
   - Move task to Completed state
   - If recurring, next instance auto-created (card appears: "Next instance created")
   - Increment completion count

2. "Continue tomorrow"
   - Task stays In-Progress
   - Prompt user: "What % complete? (optional)" — captures completion % in task metadata
   - Prompt user: "Any notes? (optional)" — captures reflective notes
   - Task will surface in "From Yesterday's Review" section of morning planning

3. "Block it"
   - Move task to Blocked state
   - Prompt: "What's blocking it? (optional notes)" — captured for user reference

4. "Park it"
   - Move task to Parked state
   - Prompt: "Any notes? (optional)" — captured for user reference

---

#### **Card Type 4: Lingering Blocked Tasks** (Appears for tasks Blocked for >7 days, threshold configurable)

**Content:** "You've had [Task Name] blocked since [date]. What would help?"

**Response Options:**
1. "Unblock & try again"
2. "It's still blocked" (reflective)
3. "Give up / Cancel"

**Actions:**
1. "Unblock & try again"
   - Move to Ready state
   - User can try again tomorrow

2. "It's still blocked"
   - Log reflection note (optional)
   - Stay Blocked; system will ask again next review

3. "Give up / Cancel"
   - Move to Cancelled state
   - Final state

---

#### **Card Type 5: Auto-Created Recurring Task** (Informational)

**Trigger:** When recurring task auto-creates after completion

**Content:** "Next instance of [Task Name] created for tomorrow"

**Responses:** Acknowledge/dismiss (informational)

**Actions:** None

---

### 6.6.1 Review Flow Mechanics

**Sequence:**
1. User initiates evening review (or is prompted at configured time)
2. System generates all applicable cards
3. Cards displayed in order: Completion, Rejections, In-Progress, Blocked, Recurring
4. User works through cards (can skip or return to any card)
5. Each response triggers its handler
6. On completion:
   - All rejection dampening resets
   - Ready for next day
   - Morning planning will show carry-overs and new cards

**Important:** Notes captured during review are purely reflective—system does NOT process them algorithmically. They exist for user's own context next day.

---

## 7. Scoring Algorithm (Implementation Notes)

### 7.1 Weighted Score Calculation

```
Base Score = (impact_weight × impact_value) + 
             (Urgency_weight × Urgency_value) + 
             (Strategic_Nudge_boost if A3 or A4, else 0)

With Dampening = Base Score / (1 + dampening_factor if rejected)

With Daily Priority = With_Dampening × (Priority_multiplier if in Today's Priorities, else 1.0)

Final Score = With Daily Priority
```

**Configurable Parameters:**
- `impact_weight` = 2.0 (default; A=4, B=3, C=2, D=1; multiply by weight)
- `Urgency_weight` = 1.5 (default; 1=4, 2=3, 3=2, 4=1; multiply by weight)
- `Strategic_Nudge_boost` = 1.5 (default; multiply base score if impact=A AND Urgency>=3)
- `Dampening_factor` = 0.5 (default; reject reduces score to 67% of original)
- `Priority_multiplier` = 2.0 (default; selected in morning planning gets 2x boost)

### 7.2 Selection Mechanism

**For "What Next?" (Single Candidate):**
1. Calculate final score for each Ready task
2. Normalize scores to probabilities (sum to 1.0)
3. Randomly select using weighted roulette wheel (not deterministic max)
4. Result: One suggestion per call

**For Morning Planning (Ranked List):**
1. Calculate final score for each Ready task
2. Sort descending by score (deterministic ranking)
3. Display as ranked list with score transparency
4. User selects which to prioritize for the day

### 7.3 Strategic Nudge Rationale

- A-impact tasks often deprioritized due to no due date (no urgency pressure)
- Strategic nudge probabilistically surfaces these to prevent value misalignment
- Boost is subtle and randomized; never enforces task selection
- Only applies to A-impact + Urgency 3 or 4

---

## 8. Dampening Scope & Reset Triggers

**Rejection Dampening:**
- Applied when user rejects task with "Not now, suggest another"
- Scope: Lasts until **next Break action** OR **next Evening Review** (whichever first)
- Can be rejected multiple times in same session; dampening stacks or increases (TBD: implementation detail)

**Break Action:**
- User selects "I'll take a break"
- Effect: Clears all rejection dampening for the current session
- Semantics: User is resetting their energy/context; ready to see full priorities again

**Evening Review:**
- Implicitly clears all rejection dampening
- New day, fresh slate
- Morning planning suggests from full pool again

---

## 9. Task State Transitions (Detailed)

| From | To | Triggers | Notes |
|------|-----|----------|-------|
| Ready | In Progress | User starts task or during "what next" flow | Multiple In-Progress allowed |
| Ready | Blocked | User during edit or review | Excluded from suggestions |
| Ready | Parked | User during edit or review | Excluded from suggestions |
| Ready | Cancelled | User during review (via card) | Final state |
| In Progress | Completed | User during review or task completion | If recurring, next instance auto-created |
| In Progress | Blocked | User during review or task edit | Task paused; waiting on external factor |
| In Progress | Parked | User during review or task edit | Task set aside intentionally |
| In Progress | Cancelled | User during review | Final state |
| Blocked | Ready | User unblocks via morning planning or edit | Attempt again |
| Blocked | Parked | User during review | Acknowledge it won't be tried |
| Blocked | Cancelled | User during review (via card) | Final state |
| Parked | Ready | User during morning planning or edit | Resume task |
| Parked | Cancelled | User during review or edit | Final state |
| Completed | — | Final state | No transitions out |
| Cancelled | — | Final state | No reactivation |

---

## 10. Data Model Summary

### Task Object

```
{
  id: UUID,
  title: string,
  description: string (optional),
  values: [value_id, ...],
  impact: A | B | C | D,
  urgency: 1 | 2 | 3 | 4,
  due_date: ISO8601 (optional),
  recurrence: none | daily | weekly | custom (optional),
  state: Ready | In Progress | Blocked | Parked | Completed | Cancelled,
  completion_percentage: 0-100 (optional, captured during review),
  notes: string (optional, captured during review),
  created_at: timestamp,
  updated_at: timestamp,
  completed_at: timestamp (optional)
}
```

### Value Object

```
{
  id: UUID,
  statement: string,
  archived: boolean,
  created_at: timestamp,
  updated_at: timestamp
}
```

### Review Card Object

```
{
  id: UUID,
  type: completion | rejection | in_progress | blocked | recurring,
  task_id: UUID (optional, if task-related),
  content: string,
  responses: [{ option: string, action: handler_key }, ...],
  generated_at: timestamp
}
```

---

## 11. MVP vs Nice-to-Have

| Feature | MVP | Notes |
|---------|-----|-------|
| Task creation/edit | ✅ | Short phrases, user-defined |
| Values entry/edit | ✅ | No hard limits |
| Task states (6-state model) | ✅ | Ready/In Progress/Blocked/Parked/Completed/Cancelled |
| impact/Urgency assignment | ✅ | AI suggestions, user final authority |
| Strategic nudge (A3/A4) | ✅ | Probabilistic weighting |
| Recurring tasks with auto-creation | ✅ | Daily/weekly + custom |
| Morning planning with priorities | ✅ | Ranking, drag-drop (web), checkboxes (mobile) |
| Score transparency (during planning) | ✅ | Tooltips show inputs/formula, not gamified |
| "What Next?" single candidate | ✅ | Fuzzy/stochastic selection |
| Rejection dampening (until break/review) | ✅ | Core to preventing nagging |
| "What was I doing?" context recovery | ✅ | In-Progress list view |
| Evening review with modular cards | ✅ | All 5 card types |
| Partial completion tracking | ✅ | % + notes (reflective) |
| Reflective notes on tasks | ✅ | Captured during review, not processed |
| Multi-user / task sharing | ❌ | v2 feature |
| AI task breakdown conversations | ❌ | v2 feature (card creates task, not conversation) |
| Advanced analytics / dashboards | ❌ | Avoid gamification |
| Time tracking / duration | ❌ | Deferred; difficulty learning deferred |
| Offline sync / multi-device | ❌ | v2 (single-device MVP) |
| Delegated tasks | ❌ | v2 feature |
| Mobile notifications | ❌ | Nice-to-have (basic flow can work without) |

---

## 12. Acceptance Criteria (MVP)

The MVP is considered successful if:

1. ✅ Users can create/edit tasks with title, values, impact, urgency, due date, recurrence
2. ✅ Users can define and manage values
3. ✅ Task states are accurately tracked and transition as specified
4. ✅ Morning planning displays all 4 sections with correct task filtering
5. ✅ Morning planning scoring is transparent (inputs/formula visible, no gamified numeric scores)
6. ✅ Web interface supports drag-drop priority selection; mobile supports checkboxes
7. ✅ "What Next?" presents exactly one candidate using fuzzy/stochastic selection
8. ✅ "What Next?" respects all three response options (start, suggest another, take break)
9. ✅ Rejection dampening applies only until next break or evening review
10. ✅ Break action clears all dampening without changing task state
11. ✅ "What was I doing?" displays In-Progress tasks with context
12. ✅ Evening review generates appropriate cards (completion, rejection, in-progress, blocked, recurring)
13. ✅ Each card type processes responses correctly (state transitions, note capture, task creation)
14. ✅ Partial completion % captured during review
15. ✅ Reflective notes captured and displayed to user (not processed algorithmically)
16. ✅ Recurring tasks auto-create next instance on completion
17. ✅ Blocked and Parked tasks excluded from suggestions
18. ✅ Daily priority boost applied and expired at evening review
19. ✅ User maintains full agency; no coercion or enforcement anywhere

---

## 13. Implementation Notes

### 13.1 Algorithm Configuration

All weighting factors should be configurable (not hardcoded) to allow tuning:

```yaml
scoring_weights:
  impact: 2.0
  urgency: 1.5
  strategic_nudge_boost: 1.5
  dampening_factor: 0.5
  priority_multiplier: 2.0

thresholds:
  rejection_count_for_card: 3
  blocked_days_before_card: 7
  due_date_lookahead_days: 7
  max_upcoming_due_tasks: 3

user_preferences:
  evening_review_time: "18:00" # configurable
  morning_planning_time: "08:00" # configurable
  morning_planning_prompt: true # optional nudge
```

### 13.2 Card Generation Logic

**Pseudo-logic for review:**

```
on evening_review_start:
  cards = []
  
  completions = all tasks with state Completed since last review
  cards.push(Completion_Summary_Card(completions))
  
  for each task in Ready state:
    if rejection_count(task, today) >= 3:
      cards.push(Rejection_Card(task))
  
  for each task in In_Progress state:
    cards.push(InProgress_Card(task))
  
  for each task in Blocked state:
    if days_since_blocked(task) > 7:
      cards.push(Blocked_Card(task))
  
  for each task completed today with recurrence:
    next_instance = create_next_instance(task)
    cards.push(Recurring_Card(next_instance))
  
  return cards
```

### 13.3 Rejection Dampening Implementation

**Session Boundaries:**

```
rejection_dampening = {
  task_id: {
    applied_at: timestamp,
    expires_at: "next_break" OR "next_evening_review"
  }
}

on break_action:
  clear all dampening
  reset session boundary

on evening_review_start:
  clear all dampening
  set new session boundary
```

### 13.4 Daily Priority Boost Lifecycle

```
daily_priorities = {
  date: "2025-01-01",
  task_ids: [uuid1, uuid2, ...],
  expires_at: evening_review time on same day
}

on morning_planning_save:
  store daily_priorities for today
  apply multiplier in scoring during the day

on evening_review_complete:
  clear daily_priorities
  user must re-select tomorrow
```

### 13.5 Neutral Language Guidelines

**Do use:**
- "How about working on X?"
- "Did you want to include X?"
- "X has due dates coming up"
- "You completed N tasks today"
- "What can we do to help?"

**Don't use:**
- "You should do X"
- "You must prioritize X"
- "Oops, you missed X"
- "Great job!" (gamification)
- "Only N tasks left" (artificial urgency)
- "3-day streak!" (gamification)

---

## 14. Future Considerations (v2 and Beyond)

- **Multi-user & Sharing:** Tasks shared with partner/caregiver for accountability
- **AI Breakdown Conversations:** When user selects "help break it down," launch actual AI dialog to decompose task
- **Difficulty Learning:** Track task completion times and difficulty trends; influence suggestions
- **Energy Level Detection:** Optional user input on energy/mood; influence suggestion weighting
- **Mobile Notifications:** Optional push alerts for "what next" suggestions
- **Offline Sync:** Local-first storage with cloud sync for multi-device
- **Advanced Analytics:** Value-based journaling without gamification (e.g., "Last 30 days, you focused on X")
- **Custom Recurrence Patterns:** Beyond daily/weekly (e.g., biweekly, monthly, "every 3 days")

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-29 | Product Owner | Initial MVP Requirements |
| 2.0 | 2025-12-30 | Product Owner | Refined spec: Ready state, Cancelled state, morning planning, review cards, dampening scope, daily priorities, score transparency |
