import { useState } from "react";
import { Stack, TextField, Label } from "@fluentui/react";
import {Send28Filled, Search24Filled} from "@fluentui/react-icons";
import { getPatientOldApi, GetPatientResponse, GetPatientRequest } from "../../api";

import styles from "./PatientQuestionInput.module.css";

interface Props {
    onSend: (patientCode: string, question: string) => void;
    onPatientCodeChanged: (patientCode: string) => void;
    onPatientNameChanged: (patientName: string) => void;
    disabled: boolean;
    placeholder?: string;
    clearOnSend?: boolean;
}

// TODO PatientCodeInput.tsx との共通化

export const PatientQuestionInput = ({ onSend, onPatientCodeChanged, onPatientNameChanged, disabled, placeholder, clearOnSend }: Props) => {
    const [patientCode, setPatientCode] = useState<string>("");
    const [question, setQuestion] = useState<string>("");
    const [name, setName] = useState<string>("");

    const makeApiRequest = async (patientCode: string) => {
        setName("");
        try {
            const request: GetPatientRequest = {
                patient_code: patientCode,
            };
            const result = await getPatientOldApi(request);
            setName(result.name)
        } catch (e) {
            setName("-");
        } finally {
            onPatientNameChanged(name);
        }
    };
    
    const enterPatientCode = () => {
        if (disabled || !patientCode.trim()) {
            return;
        }

        // 患者名検索
        makeApiRequest(patientCode);
        onPatientCodeChanged(patientCode);
    };

    const onPatientCodeEnterPress = (ev: React.KeyboardEvent<Element>) => {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            enterPatientCode();
        }
    };

    const onPatientCodeChange = (_ev: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
        if (!newValue) {
            setPatientCode("");
        } else if (newValue.length <= 1000) {
            setPatientCode(newValue);
        }
    };

    const onBlue = () => {
        // 患者名検索
        makeApiRequest(patientCode);
        onPatientCodeChanged(patientCode);
    };

    const enterPatientCodeDisabled = disabled || !patientCode.trim();

    const sendQuestion = () => {
        if (disabled || !question.trim()) {
            return;
        }

        onSend(patientCode, question);

        if (clearOnSend) {
            setQuestion("");
        }
    };

    const onQuestionEnterPress = (ev: React.KeyboardEvent<Element>) => {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            sendQuestion();
        }
    };

    const onQuestionChange = (_ev: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
        if (!newValue) {
            setQuestion("");
        } else if (newValue.length <= 1000) {
            setQuestion(newValue);
        }
    };

    const sendQuestionDisabled = disabled || !question.trim();
    
    return (
        <Stack>
            <Stack horizontal>
                <Stack horizontal className={styles.patientCodeInputContainer}>
                    <TextField
                        className={styles.patientCodeInputTextArea}
                        placeholder="患者番号を入力してください (e.g. 0000-123456)"
                        multiline={false}
                        resizable={false}
                        borderless
                        value={patientCode}
                        onChange={onPatientCodeChange}
                        onKeyDown={onPatientCodeEnterPress}
                        onBlur={onBlue}
                    />
                    <div className={styles.patientCodeInputButtonsContainer}>
                        <div
                            className={`${styles.patientCodeInputSendButton} ${enterPatientCodeDisabled ? styles.patientCodeInputSendButtonDisabled : ""}`}
                            aria-label="Search patient button"
                            onClick={enterPatientCode}
                        >
                            <Search24Filled primaryFill="rgba(115, 118, 225, 1)" />
                        </div>
                    </div>
                </Stack>
                <Label>　患者名：</Label>
                <Label>{name}</Label>
            </Stack>
            <Stack horizontal className={styles.patientQuestionInputContainer}>
                <TextField
                    className={styles.patientQuestionInputTextArea}
                    placeholder={placeholder}
                    multiline
                    resizable={false}
                    borderless
                    value={question}
                    onChange={onQuestionChange}
                    onKeyDown={onQuestionEnterPress}
                />
                <div className={styles.patientQuestionInputButtonsContainer}>
                    <div
                        className={`${styles.patientQuestionInputSendButton} ${sendQuestionDisabled ? styles.patientQuestionInputSendButtonDisabled : ""}`}
                        aria-label="Ask question button"
                        onClick={sendQuestion}
                    >
                        <Send28Filled primaryFill="rgba(115, 118, 225, 1)" />
                    </div>
                </div>
            </Stack>
        </Stack>
);
};
