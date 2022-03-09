import { useState, useMemo } from 'react';
import { MapContainer, TileLayer, useMap, Polyline } from 'react-leaflet';
import { Layout, Input, List } from 'antd';
import './App.css';

const { Header, Content, Footer, Sider } = Layout;
const { Search } = Input;

function Rivers({results}) {
  return (
    <>
      {results?.map((result, i) => <Polyline positions={result.geometry} />)}
    </>
  )
}


function App() {
  const [results, setResults] = useState();
  const [loading, setLoading] = useState(false);

  async function onSearch(value) {
    setLoading(true);
    
    const response = await fetch('http://localhost:5000/', {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        searchText: value
      })
    });
    const data = await response.json();
    
    console.log(data);
    setResults(data);
   
    setLoading(false);
  }

  return (
    <div className="App">
      <Layout style={{ minHeight: '100vh' }}>
        <Sider width={400} theme='light'>
          <Search placeholder="input search text" onSearch={onSearch} loading={loading} style={{ width: 380, marginRight: 10, marginLeft: 10, marginTop: 20 }} />
          <List
            dataSource={results}
            style={{ margin: 10 }}
            renderItem={item => (
              <List.Item>
                <List.Item.Meta
                  title={item.contents}
                  description={item.description}
                />
              </List.Item>
            )}
          />
        </Sider>
        <Layout className="site-layout">
          <MapContainer center={[43.4643, -80.5204]} zoom={13}>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <Rivers results={results}/>
          </MapContainer>
        </Layout>
      </Layout>
    </div>
  );
}

export default App;
