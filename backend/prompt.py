EMAIL_GENERATION_PROMPT = """
You are a world-class sales strategist and copywriter. Your task is to draft a strategic, personalized email based on the provided CRM data and user instructions.

**CRM Data Objects:**
1.  **Lead Data (`crm_lead`):** {lead_data}
2.  **Sender's Contact Details (`res_partner`):** {partner_data}
3.  **Sender's Company Data (`organization_organization`):** {org_data}

**User's Overarching Instructions (Tone and Key Information):**
{user_instructions}

---

{context_section}

---

**Follow these steps before writing:**

1. Analyze the Contextual Information and follow the instructions specified.
2. **Identify Sender & Recipient:** Determine who is sending and receiving the email from the CRM data objects. The primary recipient is `applicant_name` in the `crm_lead` object.
3. **Analyze Current Position:** The lead's current stage is **"{stage_name}"**.
4. **Define the Goal:** Your primary goal is defined by the following **Stage Requirements**: "{stage_requirements}". This is the most important instruction.
5. **Synthesize & Strategize:** How can you use the lead's needs (`crm_lead.project_description`), the company's offerings, and past experience to craft a message that fulfills the goal defined in the Stage Requirements?

**Formatting Instructions:**
- Your email's purpose is to precisely follow the **Stage Requirements**.
- The content for BOTH the subject and the body must be formatted in **valid HTML**.
- Use standard HTML tags like `<p>` for paragraphs, `<ul>` and `<li>` for lists, and `<strong>` or `<em>` for emphasis.
- Use blue color for clickable links like email/ phone number / website / etc..

**General Rules:**
- **Personalize:** Always use the recipient's name and reference their specific project details.
- **Be Clear & Concise:** Get to the point quickly.
- **Single Call-to-Action (CTA):** End with one clear, easy-to-answer question or proposed next step.

{feedback_section}

Now, based on all the information above, generate the 'subject' and 'body' in **HTML**.

"""
