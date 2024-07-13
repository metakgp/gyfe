import React from "react";
import metakgpLogo from "../assets/metakgp-logo.png";

const Header: React.FC = () => {
    return (
        <div className="header">
            <div className="header-logo">
                <img src={metakgpLogo} />
            </div>
            <h1 className="header-title">
                Get Your Freaking <span id="word">Electives</span>
            </h1>
        </div>
    );
};

export default Header;
