import { Example, ExampleModel } from "./Example";

import styles from "./Example.module.css";

const EXAMPLES: ExampleModel[] = [
    {
        text: "ヒュミラ（アダリムマブ）の使用による有害事象の発現率を症状別にリストアップしてください。",
        value: "ヒュミラ（アダリムマブ）の使用による有害事象の発現率を症状別にリストアップしてください。"
    },
    { text: "ヒュミラ（アダリムマブ）の有害事象の中で、特に重篤とされるものはありますか？",  
      value: "ヒュミラ（アダリムマブ）の有害事象の中で、特に重篤とされるものはありますか？"
    },
    { text: "ヒュミラ（アダリムマブ）の有害事象発現のリスクを増加させる要因や共病状態は知られていますか？", 
      value: "ヒュミラ（アダリムマブ）の有害事象発現のリスクを増加させる要因や共病状態は知られていますか？" 
    },
    { text: "ヒュミラ（アダリムマブ）の有害事象が発現した際の管理方法や対処法はどのようなものが提案されていますか？", 
      value: "ヒュミラ（アダリムマブ）の有害事象が発現した際の管理方法や対処法はどのようなものが提案されていますか？" 
    },
    { text: "ヒュミラ（アダリムマブ）の有害事象の発現率や特性は、他の同クラス薬剤と比較してどのような特徴がありますか？", 
      value: "ヒュミラ（アダリムマブ）の有害事象の発現率や特性は、他の同クラス薬剤と比較してどのような特徴がありますか？" 
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
