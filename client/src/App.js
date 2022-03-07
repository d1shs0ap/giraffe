import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { Layout, Input } from 'antd';
import './App.css';

const { Header, Content, Footer, Sider } = Layout;
const { Search } = Input;

function App() {
  async function onSearch(value) {
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
  }

  return (
    <div className="App">
      <Layout style={{ minHeight: '100vh' }}>
        <Sider width={400}>
          <Search placeholder="input search text" onSearch={onSearch} style={{ width: 400 }} />
        </Sider>
        <Layout className="site-layout">
          <MapContainer center={[51.505, -0.09]} zoom={13}>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
          </MapContainer>
        </Layout>
      </Layout>
    </div>
  );
}

export default App;
