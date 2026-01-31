import { useState, useEffect } from 'react';

function App() {
  const [markets, setMarkets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchMarkets = async () => {
      try {
        const response = await fetch('/data.json');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const jsonData = await response.json();
        
        const marketData = jsonData?.props?.pageProps?.initialState?.markets || {};
        const allMarkets = Object.values(marketData);

        const today = new Date();
        const todayStr = today.toISOString().split('T')[0];

        const todaysMarkets = allMarkets.filter(market => {
          if (!market.endDate) return false;
          const endDate = new Date(market.endDate);
          const endDateStr = endDate.toISOString().split('T')[0];
          return endDateStr === todayStr;
        });

        setMarkets(todaysMarkets);
      } catch (e) {
        setError(e.message);
        console.error("Failed to fetch or process market data:", e);
      } finally {
        setLoading(false);
      }
    };

    fetchMarkets();
  }, []);

  const MarketCard = ({ market }) => {
    return (
      <div className="bg-gray-800 rounded-lg shadow-lg overflow-hidden transition-transform transform hover:-translate-y-1">
        <img className="w-full h-40 object-cover" src={market.imgUrl} alt={market.question} />
        <div className="p-4">
          <h3 className="text-lg font-bold text-gray-100 mb-2">{market.question}</h3>
          <p className="text-sm text-gray-400">
            Expires: {new Date(market.endDate).toLocaleString()}
          </p>
        </div>
      </div>
    );
  };

  if (loading) {
    return <div className="bg-gray-900 min-h-screen flex items-center justify-center text-white">Loading markets...</div>;
  }

  if (error) {
    return <div className="bg-gray-900 min-h-screen flex items-center justify-center text-red-500">Error: {error}</div>;
  }

  return (
    <div className="bg-gray-900 min-h-screen text-white p-8">
      <header className="mb-8">
        <h1 className="text-4xl font-bold text-center">Polymarket</h1>
        <h2 className="text-2xl text-gray-400 text-center">Markets Expiring Today</h2>
      </header>
      <main>
        {markets.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {markets.map(market => <MarketCard key={market.id} market={market} />)}
          </div>
        ) : (
          <p className="text-center text-gray-500">No markets found expiring today.</p>
        )}
      </main>
    </div>
  );
}

export default App;
