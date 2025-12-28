import React from "react";

interface ListViewProps {
  items: any[];
}

const ListView: React.FC<ListViewProps> = ({ items }) => {
  if (!items || items.length === 0) {
    return <p>No items found.</p>;
  }

  return (
    <div>
      <h3>Items List</h3>
      <ul>
        {items.map((item, index) => (
          <li key={index}>
            {typeof item === "string" ? item : JSON.stringify(item)}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ListView;

