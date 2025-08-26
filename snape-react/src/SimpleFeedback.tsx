import yay from "./img/yay.png"
import confused from "./img/confused.png"

/**
 * Component containing simple sentiment feedback. Parent state is modified using callbacks provided as props.
 * @param props object props from parent.
 *  "hidden": set hidden class.
 *  "setFeedback": callback for submitting feedback to parent.
 *  "openFeedbackOptions": callback to enable triple specific feedback on parent.
 * @returns SimpleFeedback component.
 */
function SimpleFeedback(props: {
    hidden: boolean;
    mode: 'FREETEXT' | 'EMOJI';
    setFeedback: (x: string) => void;
    disabled: boolean;
}) {
    const { setFeedback, hidden, disabled} = props;


   return (
        <div className={`flexBottom ${hidden ? 'hidden' : ''}`}>
            <div
                className={`emoji ${disabled ? 'emoji-off' : ''}`}
                onClick={() => !disabled && setFeedback('-')}
            >
                <img src={confused} className="emoji-nay" />
            </div>
            <div
                className={`emoji ${disabled ? 'emoji-off' : ''}`}
                onClick={() => !disabled && setFeedback('+')}
            >
                <img src={yay} className="emoji-yay" />
            </div>
        </div>
    );
}

export default SimpleFeedback;
