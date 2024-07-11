import React from "react";

interface ModalProps {
    closeModal: React.Dispatch<React.SetStateAction<boolean>>;
}

const Modal: React.FC<ModalProps> = ({ closeModal }) => {
    return (
        <div className="modal-overlay">
            <div className="modal-content">
                <button
                    className="close-button"
                    onClick={() => closeModal(false)}
                >
                    <svg
                        fill="none"
                        viewBox="0 0 15 15"
                        height="1em"
                        width="1em"
                        className="close-button-icon"
                    >
                        <path
                            fill="currentColor"
                            fillRule="evenodd"
                            d="M11.782 4.032a.575.575 0 10-.813-.814L7.5 6.687 4.032 3.218a.575.575 0 00-.814.814L6.687 7.5l-3.469 3.468a.575.575 0 00.814.814L7.5 8.313l3.469 3.469a.575.575 0 00.813-.814L8.313 7.5l3.469-3.468z"
                            clipRule="evenodd"
                        />
                    </svg>
                </button>
                <h2>MetaKGP - GYFE</h2>
                <p>
                    GYFE simplifies course selection by providing available
                    depth and breadth electives for the upcoming semester.
                </p>
                <h4>How to get your electives?</h4>
                <ol>
                    <li>Enter your roll number and password for ERP login</li>
                    <li>Enter answer for security question and OTP</li>
                    <li>
                        Choose depth or breadth and this will download available
                        depth and breadth electives as excel sheets.
                    </li>
                </ol>
            </div>
        </div>
    );
};

export default Modal;
