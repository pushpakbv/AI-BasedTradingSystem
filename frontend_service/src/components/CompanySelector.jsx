import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, ChevronDown } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const CompanySelector = ({ currentTicker }) => {
  const navigate = useNavigate();
  const [companies, setCompanies] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');

  useEffect(() => {
    const fetchCompanies = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/companies`);
        // Expecting response.data.companies to be array of { ticker, company_name }
        setCompanies(response.data.companies);
      } catch (error) {
        console.error('Failed to fetch companies:', error);
      }
    };

    fetchCompanies();
  }, []);

  const filteredCompanies = companies.filter(company =>
    company.ticker.toLowerCase().includes(search.toLowerCase()) ||
    (company.company_name && company.company_name.toLowerCase().includes(search.toLowerCase()))
  );

  const handleSelect = (ticker) => {
    navigate(`/stock/${ticker}`);
    setIsOpen(false);
    setSearch('');
  };

  const getCurrentCompanyName = () => {
    const found = companies.find(c => c.ticker === currentTicker);
    return found ? found.company_name : currentTicker;
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2 min-w-[150px]"
      >
        <span className="font-semibold">{getCurrentCompanyName() || 'Select Company'}</span>
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full mt-2 w-64 bg-white border border-gray-300 rounded-lg shadow-lg z-20">
          {/* Search */}
          <div className="p-2 border-b">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search companies..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Company List */}
          <div className="max-h-64 overflow-y-auto">
            {filteredCompanies.length > 0 ? (
              filteredCompanies.map(company => (
                <button
                  key={company.ticker}
                  onClick={() => handleSelect(company.ticker)}
                  className={`w-full text-left px-4 py-2 hover:bg-gray-100 transition-colors ${
                    company.ticker === currentTicker ? 'bg-blue-50 text-blue-600 font-semibold' : ''
                  }`}
                >
                  <span className="font-bold">{company.company_name}</span>
                  <span className="ml-2 text-xs text-gray-500">{company.ticker}</span>
                </button>
              ))
            ) : (
              <div className="px-4 py-3 text-sm text-gray-500 text-center">
                No companies found
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default CompanySelector;