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
    { text: "入院継続に際してのお知らせ", 
      value: "入院継続に際してのお知らせ" 
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
