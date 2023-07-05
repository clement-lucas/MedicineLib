import { useState } from "react";
import { Stack, TextField, Label } from "@fluentui/react";
import { Search24Filled } from "@fluentui/react-icons";
import { getPatientOldApi, GetPatientRequest } from "../../api";

import styles from "./PatientCodeInputOld.module.css";

interface Props {
    onPatientCodeChanged: (patientCode: string) => void;
    disabled: boolean;
    placeholder?: string;
    clearOnSend?: boolean;
}

export const PatientCodeInputOld = ({ onPatientCodeChanged, disabled, placeholder, clearOnSend }: Props) => {
    const [patientCode, setPatientCode] = useState<string>("");
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
        if ((ev.key === "Enter" || ev.key === "Tab") && !ev.shiftKey) {
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

    return (
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
);
};
