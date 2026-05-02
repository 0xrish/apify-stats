import fs from 'fs';

/**
 * FETCH_ACTORS.JS (The God Tier Scraper)
 * Bypasses all limits by slicing the store by category and using safety-bypass filters.
 * Reaches 27,000+ actors.
 */

const CATEGORIES = [
    'LEAD_GENERATION', 'TRAVEL', 'SOCIAL_MEDIA', 'VIDEOS', 'AI', 'DEVELOPER_TOOLS', 
    'SEO_TOOLS', 'ECOMMERCE', 'AUTOMATION', 'NEWS', 'OPEN_SOURCE', 'JOBS', 
    'REAL_ESTATE', 'AGENTS', 'INTEGRATIONS', 'OTHER', 'MCP_SERVERS', 'BUSINESS', 'MARKETING'
];

async function fetchBatch(limit, offset, desc, category = null) {
    let url = `https://api.apify.com/v2/store?limit=${limit}&offset=${offset}&desc=${desc ? 1 : 0}&searchExcludeUnsafe=false&includeUnrunnableActors=true`;
    if (category) url += `&category=${category}`;
    
    try {
        const response = await fetch(url);
        if (!response.ok) return null;
        return await response.json();
    } catch (e) {
        return null;
    }
}

async function fetchAllActors() {
    console.log('🚀 Starting GOD TIER Apify Store Sync (27,000+ actors)...');
    
    const LIMIT = 1000;
    const allActorsMap = new Map();
    
    const initial = await fetchBatch(1, 0, false);
    if (!initial) {
        console.error('❌ API Offline');
        process.exit(1);
    }
    console.log(`📊 Global Total Discovery: ${initial.data.total}`);

    const syncSlice = async (cat = null, desc = false) => {
        let offset = 0;
        console.log(`⏳ Syncing ${cat || 'Global'} (${desc ? 'DESC' : 'ASC'})...`);
        while (offset < 16000) {
            const batch = await fetchBatch(LIMIT, offset, desc, cat);
            if (!batch || !batch.data || !batch.data.items || batch.data.items.length === 0) break;
            
            batch.data.items.forEach(a => allActorsMap.set(a.id, a));
            console.log(`   ✅ [${cat || 'Global'}] Offset ${offset}: Got ${batch.data.items.length} (Unique Total: ${allActorsMap.size})`);
            
            offset += batch.data.items.length;
            if (batch.data.items.length < 50) break;
        }
    };

    // 1. Global passes
    await syncSlice(null, false);
    await syncSlice(null, true);

    // 2. Category passes
    for (const cat of CATEGORIES) {
        await syncSlice(cat, false);
    }

    const finalActors = Array.from(allActorsMap.values());
    console.log(`\n🎉 GOD TIER SYNC COMPLETE! Collected ${finalActors.length} unique actors.`);
    
    fs.writeFileSync('./actors.json', JSON.stringify(finalActors, null, 2));
    console.log(`💾 Data saved to actors.json`);
}

fetchAllActors();
