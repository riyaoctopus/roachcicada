const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const axios = require('axios');
const path = require('path');

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

// Serve static files from the current directory
app.use(express.static(path.join(__dirname, '')));

// Zoho token management
let cachedAccessToken = null;
let tokenExpiryTime = 0;

async function getZohoAccessToken() {
    // Return cached token if valid (with 1-minute buffer)
    if (cachedAccessToken && Date.now() < tokenExpiryTime - 60000) {
        return cachedAccessToken;
    }

    try {
        const response = await axios.post('https://accounts.zoho.com/oauth/v2/token', null, {
            params: {
                client_id: process.env.ZOHO_CLIENT_ID,
                client_secret: process.env.ZOHO_CLIENT_SECRET,
                refresh_token: process.env.ZOHO_REFRESH_TOKEN,
                grant_type: 'refresh_token'
            }
        });

        if (response.data.error) {
            throw new Error(`Zoho OAuth Error: ${response.data.error}`);
        }

        cachedAccessToken = response.data.access_token;
        tokenExpiryTime = Date.now() + (response.data.expires_in * 1000);
        return cachedAccessToken;
    } catch (error) {
        console.error('Failed to get Zoho Access Token:', error.response?.data || error.message);
        throw error;
    }
}

app.post('/api/enquiry', async (req, res) => {
    try {
        const { firstName, lastName, email, phone, company, message, country, leadSource } = req.body;
        const accessToken = await getZohoAccessToken();

        const moduleName = process.env.ZOHO_MODULE_NAME || 'Cold_Calls';

        const recordData = {
            data: [
                {
                    Name: lastName || 'Not Provided',
                    Full_Name: `${firstName} ${lastName || ''}`.trim(),
                    Email: email,
                    Phone: phone,
                    Company: company || 'Not Provided',
                    Description: message,
                    Country: country,
                    Lead_Source: leadSource || 'Roach Cicada Website'
                }
            ]
        };

        const response = await axios.post(`https://www.zohoapis.com/crm/v2.1/${moduleName}`, recordData, {
            headers: {
                'Authorization': `Zoho-oauthtoken ${accessToken}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.data.data && response.data.data[0].code === 'SUCCESS') {
            return res.json({ success: true, message: 'Enquiry submitted successfully' });
        } else {
            console.error('Zoho API returned error:', response.data);
            return res.status(400).json({ success: false, error: response.data });
        }

    } catch (error) {
        console.error('Enquiry submission failed:', error.response?.data || error.message);
        return res.status(500).json({ success: false, error: 'Internal Server Error' });
    }
});

const PORT = process.env.PORT || 8000;
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});
