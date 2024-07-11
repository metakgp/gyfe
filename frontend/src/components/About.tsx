import React from "react";
import { BACKEND_URL } from "./url";
import { toast, Toaster } from "react-hot-toast";
import { useNavigate } from "react-router-dom";

interface AboutProps {
  setOpenModal: React.Dispatch<React.SetStateAction<boolean>>;
}

const About: React.FC<AboutProps> = ({ setOpenModal }) => {
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/logout`, {
        method: "GET",
        // credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }

      const responseData = await response.json();

      if (responseData.success) {
        toast.success("Logged out successfully!");
        sessionStorage.removeItem("ssoToken");
        navigate("/login");
      } else {
        throw new Error(responseData.message);
      }
    } catch (error) {
      console.error("Error logging out:", error);
      toast.error("Error logging out!");
    }
  };
  const ssoToken = sessionStorage.getItem("ssoToken");
  const loginStatus = !!ssoToken;

  return (
    <div
      className="about"
      style={
        loginStatus
          ? { display: "flex", columnGap: "1.5rem", justifyContent: "center" }
          : {}
      }
    >
      <Toaster position="bottom-center" />
      <button onClick={() => setOpenModal(true)}>Help</button>
      {loginStatus && (
        <button onClick={handleLogout} className="logout-btn">
          Logout
        </button>
      )}
    </div>
  );
};

export default About;
