import React from "react";
import { BACKEND_URL } from "./url";
import { toast } from "react-hot-toast";
import { useAppContext } from "../AppContext/AppContext";

const Electives: React.FC = () => {
    const { user } = useAppContext();

    const getElective = async (elective: string) => {
        const formData = new URLSearchParams();
        formData.append("roll_number", user.rollNo);

        try {
            const res = await fetch(`${BACKEND_URL}/elective/${elective}`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "SSO-Token": user.ssoToken!,
                },
                body: formData.toString(),
            });

            if (!res.ok) {
                toast.error("Some Error Occured. Please Try Again.");
                console.log(res.statusText);
                return;
            }

            let filename = `${user.rollNo}_${elective}.xlsx`;

            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
        } catch (error) {
            toast.error(`Error fetching ${elective} electives!`);
            console.error("Error fetching breadth electives:", error);
        }
    };

    return (
        <div className="electives-container">
            <h2>Download Electives</h2>
            <div className="electives">
                <div className="elective-item">
                    <h4>Breadth</h4>
                    <p>
                        Click download to save the excel file for available
                        breadth electives.
                    </p>
                    <button
                        className="download-button"
                        onClick={() => getElective("breadth")}
                    >
                        Download
                    </button>
                </div>
                <div className="elective-item">
                    <h4>Depth</h4>
                    <p>
                        Click download to save the excel file for available
                        depth electives.
                    </p>
                    <button
                        className="download-button"
                        onClick={() => getElective("depth")}
                    >
                        Download
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Electives;
