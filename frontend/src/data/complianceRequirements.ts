export const complianceChecklist = {
    employment_laws_my: {
        requirements: [
            "termination_clause",
            "minimum_wage_compliance",
            "overtime_provisions",
            "annual_leave_entitlement",
            "notice_period_requirements"
        ]
    },
    data_protection: {
        requirements: [
            "data_processing_notice",
            "consent_mechanism",
            "data_retention_policy"
        ]
    }
};

export type ComplianceChecklistData = typeof complianceChecklist;