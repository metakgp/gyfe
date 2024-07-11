import React from "react";
import About from "./About";

const Footer: React.FC = () => {
    return (
        <div>
            <About />
            <footer>
                <p>
                    Maintained by{" "}
                    <strong>
                        <a target="_blank" href="https://metakgp.github.io/">
                            <span className="metakgp">MetaKGP</span>
                        </a>
                    </strong>{" "}
                    with<strong> ❤️ </strong>at{" "}
                    <a target="_blank" href="https://github.com/metakgp/gyfe">
                        <strong>GitHub</strong>
                    </a>
                </p>
            </footer>
        </div>
    );
};

export default Footer;
