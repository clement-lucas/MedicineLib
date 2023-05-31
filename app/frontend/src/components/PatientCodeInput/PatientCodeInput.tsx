import { useState } from "react";
import { Stack, TextField, Label } from "@fluentui/react";
import {Send28Filled, Search24Filled} from "@fluentui/react-icons";

import styles from "./PatientCodeInput.module.css";

interface Props {
    disabled: boolean;
    placeholder?: string;
    clearOnSend?: boolean;
}

export const PatientCodeInput = ({ disabled, placeholder, clearOnSend }: Props) => {
    const [patientCode, setPatientCode] = useState<string>("");

    const enterPatientCode = () => {
        if (disabled || !patientCode.trim()) {
            return;
        }

        // TODO 患者名検索
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
            <Label>鈴木 ヨシ子</Label>
        </Stack>
);
};
