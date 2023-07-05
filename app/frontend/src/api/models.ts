export const enum Approaches {
    RetrieveThenRead = "rtr",
    ReadRetrieveRead = "rrr",
    ReadDecomposeAsk = "rda"
}

export type AskRequestOverrides = {
    semanticRanker?: boolean;
    semanticCaptions?: boolean;
    excludeCategory?: string;
    top?: number;
    temperature?: number;
    promptTemplate?: string;
    promptTemplatePrefix?: string;
    promptTemplateSuffix?: string;
    suggestFollowupQuestions?: boolean;
};

export type AskRequest = {
    question: string;
    approach: Approaches;
    overrides?: AskRequestOverrides;
};

export type DocumentRequest = {
    patientCode: string;
    documentName: string;
    approach: Approaches;
    overrides?: AskRequestOverrides;
};

export type DischargeRequest = {
    patientCode: string;
    documentName: string;
    approach: Approaches;
    overrides?: AskRequestOverrides;
};

export type AskPatientRequest = {
    patientCode: string;
    question: string;
    approach: Approaches;
    overrides?: AskRequestOverrides;
};

export type AskResponse = {
    answer: string;
    thoughts: string | null;
    data_points: string[];
    error?: string;
};

export type ChatTurn = {
    user: string;
    bot?: string;
};

export type ChatRequest = {
    history: ChatTurn[];
    approach: Approaches;
    overrides?: AskRequestOverrides;
};

export type ChatPatientTurn = {
    patientcode: string;
    bot?: string;
};

export type ChatPatientRequest = {
    history: ChatTurn[];
    history_patient: ChatPatientTurn[];
    approach: Approaches;
    overrides?: AskRequestOverrides;
};

export type GetPatientRequest = {
    patient_code: string;
};

export type GetPatientResponse = {
    name: string;
    error?: string;
};
