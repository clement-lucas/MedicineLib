import { Example, ExampleModel } from "./Example";

import styles from "./Example.module.css";

const EXAMPLES: ExampleModel[] = [
    { text: "退院時サマリ", 
      value: "退院時サマリ" 
    }
];

interface Props {
    onExampleClicked: (value: string) => void;
}

export const DischargeList = ({ onExampleClicked }: Props) => {
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
