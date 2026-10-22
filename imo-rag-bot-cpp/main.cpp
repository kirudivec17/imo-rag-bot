#include <iostream>
#include <vector>
#include <string>
#include <algorithm>
#include <fstream>
#include <filesystem>
using namespace std;
namespace fs = std::filesystem;

string toLower(string s){
    transform(s.begin(), s.end(), s.begin(), ::tolower);
    return s;
}

int main() {
    cout << "=== IMO REAL BOT - Mobile 2000 PDF Search ===\n";
    
    // Mobile ke liye path - change kar sakta hai
    vector<string> folders = {
        "/storage/emulated/0/imo_pdfs",
        "/storage/emulated/0/imo_pdfs_2",
        "/storage/emulated/0/imo_pdfs_3",
        "imo_pdfs", "imo_pdfs_2", "imo_pdfs_3", // GitHub actions ke liye
        "data/manuals"
    };

    vector<fs::path> all_pdfs;
    for(auto &folder : folders){
        if(fs::exists(folder)){
            cout << "Scan: " << folder << "\n";
            for(auto &p : fs::recursive_directory_iterator(folder)){
                if(p.is_regular_file()){
                    string ext = toLower(p.path().extension().string());
                    if(ext==".pdf" || ext==".txt"){
                        all_pdfs.push_back(p.path());
                    }
                }
            }
        }
    }

    cout << "Total PDFs found: " << all_pdfs.size() << "\n";
    if(all_pdfs.empty()){
        cout << "Folder nahi mila! /storage/emulated/0/imo_pdfs me PDF daal.\n";
        return 0;
    }

    cout << "Search kya karna hai (SCBA / EEXI / lifeboat): ";
    string query;
    getline(cin, query);
    string qlow = toLower(query);

    int found=0;
    for(auto &path : all_pdfs){
        string fname = toLower(path.filename().string());
        bool match = false;
        string where = "";

        // 1. NAAM ME SEARCH
        if(fname.find(qlow)!=string::npos){
            match = true;
            where = "FILENAME";
        }

        // 2. ANDAR KE TEXT ME SEARCH (PDF ko binary read karke)
        if(!match){
            ifstream file(path, ios::binary);
            if(file){
                // Sirf pehle 100KB padhenge - mobile tez rahega
                char buffer[102400];
                file.read(buffer, sizeof(buffer));
                string content(buffer, file.gcount());
                string clow = toLower(content);
                if(clow.find(qlow)!=string::npos){
                    match = true;
                    where = "INSIDE TEXT";
                }
            }
        }

        if(match){
            cout << "\n>> [" << where << "] " << path.filename().string() << "\n";
            cout << "   Path: " << path.string() << "\n";
            found++;
            if(found>=20) { // mobile pe 20 result ke baad rok denge
                cout << "\n--- 20 mil gaye, aur bhi hai... ---\n";
                break;
            }
        }
    }

    cout << "\n--- DONE: " << found << " files me '" << query << "' mila ---\n";
    return 0;
}
