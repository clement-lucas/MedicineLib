import { Example, ExampleModel } from "./Example";

import styles from "./Example.module.css";

const EXAMPLES: ExampleModel[] = [
    {
        text: "今までで一番高い FeNO の検査日と ppb 値を教えてください。",
        value: "今までで一番高い FeNO の検査日と ppb 値を教えてください。"
    },
    { text: "前回の投薬内容を教えてください", 
      value: "前回の投薬内容を教えてください"
    },
    { text: "切除した場所はどこ？", 
      value: "切除した場所はどこ？" 
    }
];

interface Props {
    onExampleClicked: (value: string) => void;
}

export const PatientExampleList = ({ onExampleClicked }: Props) => {
    return (
        <ul className={styles.examplesNavList}>
            {EXAMPLES.map((x, i) => (
                <li key={i}>
                    <Example text={x.text} value={x.value} onClick={onExampleClicked} />
                </li>
            ))}
        </ul>
    );
};
