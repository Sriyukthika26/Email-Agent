from concurrent.futures import ThreadPoolExecutor
from datamodels import AgentState
from datafetch import datafetch
from projectsfetch import fetch_projects
from helper_functions import filter_id_fields

def fetch_with_concurrency(state: AgentState) -> AgentState:
    """
    Fetch required CRM data using concurrent API requests.
    IDs are sanitized with int() before query interpolation.
    """
    print("\n--- FETCHING DATABASE INFO (concurrent) ---")

    try:
        lead_id = int(state.get("lead_id"))
        user_id = int(state.get("user_id"))
        print(f"Sanitized lead_id={lead_id}, user_id={user_id}")

    except (TypeError, ValueError):
        return {**state, "error_message": "Invalid lead_id or user_id provided"}

    db_data = {}

    try:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}

            # 1. User → company_id + partner_id
            user_query = f"SELECT company_id, partner_id FROM res_users WHERE id = {user_id};"
            print(f"Fetching user info for user_id={user_id}")
            futures["user"] = executor.submit(datafetch, user_query)

            # Run user query first (we need company_id + partner_id)
            user_result = futures["user"].result()
            if not user_result:
                return {**state, "error_message": f"No user found for user_id: {user_id}"}

            company_id = int(user_result[0]["company_id"])
            partner_id = int(user_result[0]["partner_id"])
            print(f"✔ User found → company_id={company_id}, partner_id={partner_id}")

            # 2. Partner
            partner_query = f"""
                SELECT name, title, complete_name, ref, tz, vat, company_registry,
                       website, function, type, street, street2, zip, city, email,
                       phone, mobile, commercial_company_name, company_name, barcode,
                       comment, active, employee, contact_address_complete,
                       email_normalized, street_name, street_number, street_number2
                FROM res_partner WHERE id = {partner_id};
            """
            print(f"Fetching partner info for partner_id={partner_id}")
            futures["partner"] = executor.submit(datafetch, partner_query)

            # 3. Organization
            org_query = f"SELECT * FROM organization_organization WHERE company_id = {company_id};"
            print(f"Fetching organization info for company_id={company_id}")
            futures["organization"] = executor.submit(datafetch, org_query)

            # 4. Lead
            lead_query = f"""
                SELECT name, address, city, region, project_class, project_status, project_type, project_description, builder_name,
                       builder_email, owner_company, owner_phone, owner_name, owner_email, applicant_name, applicant_company,
                       applicant_phone, applicant_email, contact_name, partner_name, email_from, email_domain_criterion,
                       email_cc, type, priority, phone, mobile, website, street, street2, zip, city, date_deadline,
                       lead_properties, description, expected_revenue, prorated_revenue, recurring_revenue,
                       recurring_revenue_monthly, recurring_revenue_monthly_prorated, recurring_revenue_prorated,
                       day_open, day_close, probability, automated_probability, won_status, days_to_convert,
                       days_exceeding_closing, month_started, permit_issue_date, cost_of_construction,
                       additional_info, project_year, is_lead_lost, lost_feedback, stage_id
                FROM crm_lead WHERE id = {lead_id};
            """
            print(f"Fetching lead info for lead_id={lead_id}")
            futures["lead"] = executor.submit(datafetch, lead_query)

        # Collect results
        partner_records = futures["partner"].result()
        org_records = futures["organization"].result()
        lead_records = futures["lead"].result()

        if not partner_records:
            return {**state, "error_message": f"No partner contact found for partner_id: {partner_id}"}
        if not org_records:
            return {**state, "error_message": f"No organization found for company_id: {company_id}"}
        if not lead_records:
            return {**state, "error_message": f"No lead found for lead_id: {lead_id}"}

        print("✔ Partner, organization, and lead data fetched")

        db_data["res_partner"] = partner_records[0]
        db_data["organization"] = filter_id_fields(org_records[0])
        db_data["crm_lead"] = lead_records[0]

        # Fetch stage if present
        stage_id = lead_records[0].get("stage_id")
        if stage_id:
            try:
                stage_id = int(stage_id)
                print(f"Fetching stage info for stage_id={stage_id}")
                stage_query = f"SELECT name, requirements FROM crm_stage WHERE id = {stage_id};"
                stage_records = datafetch(stage_query)
                db_data["crm_stage"] = stage_records[0] if stage_records else None
                print("✔ Stage data fetched")
            except ValueError:
                db_data["crm_stage"] = None
        else:
            db_data["crm_stage"] = None
            print("No stage linked with this lead")

        # Conversation / Past projects
        print("Checking if lead has conversation history...")
        latest_message_query = f"""
            SELECT parent_id FROM mail_message
            WHERE model = 'crm.lead' AND res_id = {lead_id}
            ORDER BY date DESC LIMIT 1;
        """
        latest_message = datafetch(latest_message_query)

        if not latest_message or not latest_message[0].get("parent_id"):
            print("No conversation found → fetching past projects")
            past_projects_data = fetch_projects(company_id=company_id, limit=20)
            raw_projects = past_projects_data.get("data", {}).get("projects", []) if past_projects_data else []
            db_data["past_projects"] = [
                {
                    "projectName": p.get("projectName"),
                    "serviceType": p.get("serviceType"),
                    "projectType": p.get("projectType"),
                    "builderName": p.get("builderName"),
                    "builderEmail": p.get("builderEmail"),
                    "projectAddress": p.get("projectAddress"),
                    "city": p.get("city"),
                    "country": p.get("country"),
                    "region": p.get("region"),
                }
                for p in raw_projects
            ]
            db_data["conversation_history"] = []
            print(f"✔ Past projects fetched ({len(db_data['past_projects'])} projects)")
        else:
            print("Conversation found → fetching full history")
            history_query = f"""
                SELECT id, parent_id, email_from, subject, body, date
                FROM mail_message
                WHERE model = 'crm.lead' AND res_id = {lead_id}
                ORDER BY date DESC;
            """
            conversation_records = datafetch(history_query)
            db_data["conversation_history"] = conversation_records if conversation_records else []
            db_data["past_projects"] = []
            print(f"✔ Conversation history fetched ({len(db_data['conversation_history'])} messages)")

        print("--- FETCH COMPLETE ---\n")
        return {"db_data": db_data, "error_message": None}

    except Exception as e:
        error_type = type(e).__name__
        print(f"❌ Error in fetch_with_concurrency: {error_type} - {e}")
        return {"db_data": None, "error_message": f"Unexpected error ({error_type}): {e}"}
