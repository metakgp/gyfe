import React from 'react';

interface ModalProps {
    closeModal: React.Dispatch<React.SetStateAction<boolean>>;
}

const Modal: React.FC<ModalProps> = ({closeModal}) => {
    return (
        <div className='modalBackground'>
            <div className='modalContainer'>
                <div className='popup-title'>
                    <h2 style={{display: 'inline'}}>MetaKGP - GYFE</h2>
                    <button onClick={() => closeModal(false)}>x</button>
                </div>
                <div className='popup-body'>
                    <p>Struggling to plan your semester? GYFE simplifies course selection by providing available depth and breadth electives for the upcoming semester. No more searching through endless course catalogs in ERP - just a few clicks and you'll be well on your way to crafting the perfect schedule!<br/><h4>How to get your electives?</h4>Enter your roll number and password for ERP login. Then enter answer for security question and OTP as prompted. After this, you will get an option to download the available depth and breadth electives as excel sheets.</p>
                </div>
            </div>
        </div>
    );
}

export default Modal;