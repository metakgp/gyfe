import React from 'react';
import metakgpLogo from '../assets/header-logo.png';

const Header: React.FC = () => {
    return(
        <div className='header'>
            <div className='header-logo'><img src={metakgpLogo}/></div>
            <div className='title'><h1>Get Your Freaking <span id='word'>Electives</span></h1></div>
        </div>
    );
}

export default Header