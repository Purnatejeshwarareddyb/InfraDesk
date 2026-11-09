# Project report outline

Write each section from your own work. Evidence must be real screenshots or output from your machine (see `reports/evidence/README.md`).

1. Title page and declaration
2. Certificate and acknowledgement
3. Abstract
4. Table of contents, list of figures and tables
5. Introduction (problem, motivation)
6. Objectives and scope (and what is out of scope)
7. Literature / existing systems survey
8. Requirements (functional, non-functional, roles)
9. System analysis (use cases, workflow, status table: `docs/workflow.md`)
10. System design (architecture, database design, API design: `docs/architecture.md`, `database-design.md`, `api-reference.md`)
11. Implementation: backend
12. Implementation: frontend
13. Security design (`docs/security.md`)
14. DevOps: Docker Compose, Terraform, Puppet, Ansible, Nagios and their ownership boundaries
15. Offline operation (`docs/offline-operation.md`)
16. Testing: plan, test cases, real results (`testing-plan.md`, your own filled `test-results-template.md`)
17. Results and screenshots
18. Limitations and risks
19. Future work
20. Conclusion
21. References and appendices (commands, configuration listings)

## Evidence screenshot checklist
Login; admin dashboard; worker dashboard; ticket creation; ticket history; assignment; notifications; reports; CSV file; activity log; `pytest` output; `npm test` output; browser E2E output; `docker compose ps`; `/ready`; backup file; Terraform validate/plan/apply; Puppet two applies; Ansible deploy twice and validate; Nagios OK, CRITICAL, OK; offline run.
Only include items you actually captured.
