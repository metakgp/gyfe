import React from "react";
import Header from "./components/Header";
import Footer from "./components/Footer";
import MultiForm from "./components/MultiForm";
import { Toaster } from "react-hot-toast";

const App: React.FC = () => {
    return (
        <>
            <Toaster position="bottom-center" />
            <div>
                <Header />
                <MultiForm />
            </div>
            <Footer />
        </>
    );
};

export default App;
