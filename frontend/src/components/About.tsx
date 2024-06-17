import React from 'react';

interface AboutProps {
    setOpenModal: React.Dispatch<React.SetStateAction<boolean>>;
}

const About: React.FC<AboutProps> = ({setOpenModal}) => {
    return (
        <div className='about'>
            <button onClick={() => setOpenModal(true)}>Help</button>
        </div>
    );
}

export default About;