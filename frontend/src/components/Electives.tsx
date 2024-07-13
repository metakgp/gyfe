import React, { useState } from "react";
import { BACKEND_URL } from "./url";
import { toast } from "react-hot-toast";
import { useAppContext } from "../AppContext/AppContext";
import Spinner from "./Spinner";

const Electives: React.FC = () => {
    const { user } = useAppContext();
    const [isBreadthDownloading, setIsBreadthDownloading] = useState(false);
    const [isDepthDownloading, setIsDepthDownloading] = useState(false);
    const getElective = async (elective: string) => {
        const formData = new URLSearchParams();
        formData.append("roll_number", user.rollNo);
        {
            elective == "breadth"
                ? setIsBreadthDownloading(true)
                : setIsDepthDownloading(true);
        }

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
        } finally {
            {
                elective == "breadth"
                    ? setIsBreadthDownloading(false)
                    : setIsDepthDownloading(false);
            }
        }
    };

    return (
        <div className="electives-container">
            <h2>Download Electives</h2>
            <p>
                Below are the depth and breadth electives available for you for
                subject registration
            </p>
            <div className="electives">
                <button
                    className="download-button"
                    onClick={() => getElective("breadth")}
                    disabled={isBreadthDownloading}
                >
                    {isBreadthDownloading ? <Spinner /> : "Download Breadth"}
                </button>
                <button
                    className="download-button"
                    onClick={() => getElective("depth")}
                    disabled={isDepthDownloading}
                >
                    {isDepthDownloading ? <Spinner /> : "Download Depth"}
                </button>
            </div>
        </div>
    );
};

export default Electives;
