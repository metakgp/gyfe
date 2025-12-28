import React, { useState, useEffect } from "react";
import ListView from "./components/ListView";
import Header from "./components/Header";
import Footer from "./components/Footer";
import MultiForm from "./components/MultiForm";
import { Toaster } from "react-hot-toast";
import Circles from "./components/Circles";
import hero from "./assets/hero-img.png";
import Modal from "./components/Modal";

const App: React.FC = () => {
  const [openModal, setOpenModal] = useState(false);
  const [items, setItems] = useState<any[]>([]);

  useEffect(() => {
    fetch("/api/list")
      .then((res) => res.json())
      .then((data) => setItems(data))
      .catch((err) => console.error(err));
  }, []);

  return (
    <>
      <main>
        <Toaster position="bottom-center" />
        <Circles />

        <div id="wrapper">
          <div className="wrapper-item">
            <div id="wrapped">
              <Header />
              <MultiForm />

              {/* LIST RENDERED HERE */}
              <ListView items={items} />
            </div>

            <Footer openModal={setOpenModal} />
          </div>

          <aside>
            <img src={hero} alt="hero" />
          </aside>
        </div>
      </main>

      {openModal && <Modal closeModal={setOpenModal} />}
    </>
  );
};

export default App;
