import { Example, ExampleModel } from "./Example";

import styles from "./Example.module.css";

const EXAMPLES: ExampleModel[] = [
    {
        text: "看護記録",
        value: "看護記録"
    },
    { text: "紹介状", 
      value: "紹介状"
    },
    { text: "入院経過", 
      value: "入院経過" 
    }
];

interface Props {
    onExampleClicked: (value: string) => void;
}

export const DocumentList = ({ onExampleClicked }: Props) => {
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
