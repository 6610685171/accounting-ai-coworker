# AI Accounting Copilot Implementation Plan (6 Weeks)

The goal is to develop an AI Coworker (AR Module) for an accounting team over a 6-week period by extending the open-source Eigent framework. The system will handle meter readings via OCR, automate Excel data entry, generate FlowAccount invoices via MCP, and provide flexible LINE notifications, all orchestrated through a multi-agent architecture with human-in-the-loop checkpoints.

## User Review Required
> [!IMPORTANT]
> - Please review the multi-agent architecture proposed for the OCR and Excel integration.
> - Please confirm if the breakdown of tasks across the 6 weeks aligns with your expectations and technical constraints.

## Open Questions
> [!WARNING]
> 1. **API Keys:** Do you already have the Claude Vision / GPT-4o API keys and LINE OA Token available, or should we mock these for the initial development phases?
> 2. **FlowAccount:** How should we handle the integration of FlowAccount MCP initially? Will we test it against a sandbox/developer account?
> 3. **Eigent Platform:** Are we working within a specific branch or existing fork of the Eigent repository, or will we be initializing a fresh clone during Week 1?

## Proposed Changes

### Week 1: Foundation & Thai Localization
- **[MODIFY]** `locales/` or `i18n/` files in the Eigent frontend to translate UI elements to Thai.
- **[NEW]** Setup backend folder structures for `/meter-photos/` (inbox, processed, archive), `/excel-files/` (template, monthly), `/output/invoices/`, and `/config/`.
- **[NEW]** `scripts/excel_test.py`: A Python script to verify reading/writing to the company's existing `.xlsx` template using `openpyxl` without breaking formulas or formatting.
- **[MODIFY]** Customer database structure to add `LINE_USER_ID`, `DELIVERY_MODE`, and `CONTACT_PREFERENCE`.

### Week 2: Feature 1 - Meter Reader Copilot (Multi-Agent)
- **[NEW]** `agents/file_watcher.py`: Agent to monitor `/meter-photos/inbox/`, parse file names, and move files to `/processed/`.
- **[NEW]** `agents/ocr_reader.py`: Agent to call Vision API and extract meter readings in JSON format.
- **[NEW]** `agents/excel_writer.py`: Agent to duplicate previous month's meter value, enter the new value, calculate utility costs (Water=20, Elec=7, Tax=70/50), embed resized images, and save as a new file.
- **[NEW]** `agents/qc_checker.py`: Agent to validate extracted data (e.g., new > old) and report anomalies to the user.

### Week 3: Feature 2 - Invoice Draft Copilot & FlowAccount MCP
- **[NEW]** Connect and configure FlowAccount MCP.
- **[NEW]** `scripts/data_extractor.py`: Python script to extract billing amounts from the finalized Excel sheet and map them to JSON for FlowAccount.
- **[NEW]** `agents/invoice_creator.py`: Agent to use FlowAccount MCP to create draft invoices based on extracted Excel data.
- **[NEW]** `agents/invoice_verifier.py`: Agent to double-check the created FlowAccount drafts against the Excel data.

### Week 4: Human-in-the-Loop Integration
- **[MODIFY]** Eigent native UI workflows to introduce 3 Approval Gates:
  - **Gate 1:** Post-OCR & Excel Entry (Approve or Request Edits).
  - **Gate 2:** Post-FlowAccount Draft (Confirm drafts).
  - **Gate 3:** Pre-LINE Delivery (Review messages).

### Week 5: Flexible LINE Delivery
- **[NEW]** `LINE_Templates` sheet added to the Excel database for easy customization of notification messages.
- **[NEW]** `agents/delivery_agent.py`: Agent to handle the delivery flow.
  - **Manual Mode:** Prepares images/PDFs and formatted markdown for the accountant to copy-paste.
  - **Automated Mode:** Uses `LINE_OA_TOKEN` to push messages directly to customers via API.

### Week 6: Polish, Edge Cases & Demo
- **[MODIFY]** Add robust error handling (e.g., blurred photos, API timeouts, missing LINE IDs).
- **[NEW]** `docs/USER_GUIDE.md`: A concise manual covering photo naming conventions, template editing, and error resolution.
- **[NEW]** Demo scripts and sample data setup for the final presentation.

## Verification Plan

### Automated Tests
- `pytest tests/test_ocr_parser.py`: Verify that the Vision API parsing correctly formats JSON output.
- `pytest tests/test_excel_writer.py`: Ensure openpyxl updates formulas correctly and embeds images without corruption.

### Manual Verification
- Test End-to-End workflow using 3-5 sample photos and a mock Excel file.
- Verify human-in-the-loop triggers pause the agent execution and resume upon user approval.
- Confirm FlowAccount drafts appear correctly in the FlowAccount web UI.
