import { Example, ExampleModel } from "./Example";

import styles from "./Example.module.css";

const EXAMPLES: ExampleModel[] = [
    {
        text: "What is the side effects of cancer treatment in children?",
        value: "What is the side effects of cancer treatment in children?"
    },
    { text: "What is the effective dose of FPD for gastric cancer screening?", 
      value: "What is the effective dose of FPD for gastric cancer screening?"
    },
    { text: "小児がん治療についての情報を教えてください", 
      value: "小児がん治療についての情報を教えてください" 
    }
];

interface Props {
    onExampleClicked: (value: string) => void;
}

export const ExampleList = ({ onExampleClicked }: Props) => {
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
