#include <iostream>
#include <vector>
#include <string>
#include <algorithm>
#include <fstream>
#include <filesystem>
using namespace std;
namespace fs = std::filesystem;

int main() {
    cout << "=== IMO RAG BOT - C++ (2000+ PDFs Real) ===\n";
    
    vector<pair<string,string>> docs;
    // Try to load your summary files which already exist in repo
    vector<string> index_files = {"all_pdf_list.txt", "imo_public_summary.csv", "pdf_list.txt"};
    
    for(auto &idx : index_files) {
        if(fs::exists(idx)) {
            ifstream f(idx);
            string line;
            while(getline(f, line)) {
                if(line.size()>10) docs.push_back({idx, line});
            }
        }
    }
    // Also scan imo_pdfs folders for names
    for(auto &folder : {"imo_pdfs", "imo_pdfs_2", "imo_pdfs_3"}) {
        if(fs::exists(folder)) {
            for(auto &p : fs::directory_iterator(folder)) {
                docs.push_back({p.path().filename().string(), p.path().string()});
            }
        }
    }

    cout << "Total indexed from your repo: " << docs.size() << " entries\n";
    cout << "Search (ex: SCBA, EEXI, MARPOL): ";
    string query;
    getline(cin, query);
    string q = query;
    transform(q.begin(), q.end(), q.begin(), ::tolower);

    int found=0;
    for(auto &d : docs) {
        string low = d.second;
        transform(low.begin(), low.end(), low.begin(), ::tolower);
        if(low.find(q) != string::npos) {
            cout << "\n>> " << d.first << " : " << d.second.substr(0,200) << "\n";
            found++;
            if(found>=10) break;
        }
    }
    cout << "\nTotal found: " << found << " / " << docs.size() << endl;
    return 0;
}
