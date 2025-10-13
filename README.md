# QuantNetX

A comprehensive quantitative analytics platform for cryptocurrency options and derivatives markets. Real-time data analysis, risk metrics, and advanced visualization tools.

## Overview

QuantNetX provides professional-grade quantitative analysis tools for cryptocurrency derivatives. Currently featuring implied probability distributions from options prices using real-time Deribit API data.

## Current Features

### 📊 Implied Probability Distribution Dashboard

Extract risk-neutral probability distributions from options market prices using the butterfly spread approach (second derivative method):

- **Implied Probability Distribution**: Risk-neutral probability density derived from call and put options
- **Cumulative Distribution Function**: Cumulative probabilities for different strike prices
- **Option Price Derivatives**: Mark prices, first derivatives (delta), and second derivatives (gamma)

## Roadmap

🚀 **Coming Soon:**
- Risk metrics (VaR, CVaR, Greeks)
- Volatility surface analysis
- Open interest analysis
- Historical volatility vs implied volatility
- Position sizing calculators
- Multi-asset correlation analysis

## Features

- ✅ Real-time data from Deribit API
- ✅ Support for BTC and ETH options
- ✅ Accurate second derivative calculation for non-uniformly spaced strikes
- ✅ Separate analysis for calls and puts
- ✅ Interactive Plotly charts with zoom and pan
- ✅ Dark theme, responsive design
- ✅ Zero dependencies (single HTML file)
- ✅ No build process required

## Quick Start

### Local Development

Simply open `index.html` in your browser, or serve it with any static file server:

```bash
# Python
python3 -m http.server 8000

# Node.js
npx serve

# PHP
php -S localhost:8000
```

Then navigate to `http://localhost:8000`

### Deploy to GitHub Pages

1. Create a new repository on GitHub
2. Push this code to the repository
3. Go to Settings → Pages
4. Select "Deploy from a branch"
5. Choose "main" branch and "/ (root)"
6. Save and wait for deployment

Your dashboard will be available at: `https://yourusername.github.io/quantnetx/`

### Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd quantnetx
vercel
```

Or use the [Vercel Dashboard](https://vercel.com) to import your repository directly.

### Deploy to Netlify

1. Drag and drop the folder to [Netlify Drop](https://app.netlify.com/drop)
2. Or connect your GitHub repository at [netlify.com](https://netlify.com)

## Technical Details

### Methodology

The implied probability distribution is calculated using the Breeden-Litzenberger formula:

```
P(K) = d²C/dK²
```

Where:
- `P(K)` is the probability density at strike K
- `C` is the call option price as a function of strike
- The second derivative is computed using finite differences for non-uniformly spaced strikes

For non-uniformly spaced points (xa, xb, xc) with values (fa, fb, fc):

```
f''(xb) = 2 * (fa * d2 + fc * d1 - fb * (d1 + d2)) / (d1 * d2 * (d1 + d2))
```

Where `d1 = xb - xa` and `d2 = xc - xb`.

The distribution is then normalized so that the probabilities sum to 1.

### Data Source

Options data is fetched in real-time from the [Deribit API](https://www.deribit.com/api/v2/):

- **Endpoint**: `GET /api/v2/public/get_book_summary_by_currency`
- **Parameters**:
  - `currency`: BTC or ETH
  - `kind`: option
- **Rate Limits**: Public API, no authentication required
- **Data**: Mark prices, implied volatility, strikes, open interest

### File Structure

```
quantnetx/
├── index.html          # Main dashboard (self-contained)
├── README.md           # This file
├── LICENSE             # MIT License
└── .gitignore         # Git ignore file
```

## Browser Compatibility

- ✅ Chrome/Edge (v90+)
- ✅ Firefox (v88+)
- ✅ Safari (v14+)
- ✅ Mobile browsers

Requires JavaScript enabled and internet connection for API access.

## API Usage

The dashboard makes direct calls to Deribit's public API. No API key is required, but be aware of rate limits:

- Public endpoints: ~20 requests per second
- No authentication needed
- CORS-enabled

## Development

The entire application is contained in a single `index.html` file with:

- Embedded CSS styles
- Embedded JavaScript (no external dependencies except Plotly CDN)
- No build process
- No package manager needed

To modify:

1. Edit `index.html` directly
2. Refresh your browser to see changes
3. All code is vanilla JavaScript (ES6+)

### Code Structure

The JavaScript is organized into sections:

1. **Global Variables**: API constants and state
2. **Date/Time Utilities**: Expiry date parsing
3. **API Data Fetching**: Deribit API integration
4. **Probability Calculations**: Core probability math
5. **Derivative Calculations**: For visualization
6. **UI Utilities**: Formatting and helpers
7. **UI Updates**: Stats display
8. **Plotting Functions**: Plotly charts
9. **Event Handlers**: User interactions
10. **Event Listeners**: UI event bindings
11. **Initialization**: Page load

## Contributing

Contributions are welcome! Feel free to:

- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation

## License

MIT License - see LICENSE file for details

## Disclaimer

This platform is for educational and research purposes only. The analytics and metrics provided should not be interpreted as investment advice.

Options trading involves substantial risk. Always do your own research and consult with financial professionals before making investment decisions.

## Resources

- [Deribit API Documentation](https://docs.deribit.com/)
- [Breeden-Litzenberger Formula](https://en.wikipedia.org/wiki/Risk-neutral_measure)
- [Option Implied Probability Distributions](https://www.investopedia.com/terms/i/implied-probability.asp)
- [Plotly.js Documentation](https://plotly.com/javascript/)

## About

**QuantNetX** - Quantitative Analytics for the Next Generation

Built for traders, researchers, and quants who need professional-grade tools for cryptocurrency derivatives analysis.

---

**Tech Stack**: Vanilla JavaScript, Plotly.js, Deribit API
