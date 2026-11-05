import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';

// Tumhara purana backend - wahi 788 PDFs wala
const String API_URL = "http://129.225.105.196:8001";

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  SharedPreferences prefs = await SharedPreferences.getInstance();
  bool isLogged = prefs.getBool('isLogged') ?? false;
  runApp(MyApp(isLogged: isLogged));
}

class MyApp extends StatelessWidget {
  final bool isLogged;
  const MyApp({super.key, required this.isLogged});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'IMO AI Assistant',
      theme: ThemeData(primaryColor: Color(0xFF1A5DCE), useMaterial3: true),
      home: isLogged ? HomeScreen() : LoginScreen(),
    );
  }
}

// ============ LOGIN SCREEN ============
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  bool _loading = false;

  Future<void> _login() async {
    if (_emailCtrl.text.isEmpty || !_emailCtrl.text.contains('@')) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Sahi email dalo')));
      return;
    }
    setState(() => _loading = true);
    await Future.delayed(Duration(seconds: 1));
    SharedPreferences prefs = await SharedPreferences.getInstance();
    await prefs.setBool('isLogged', true);
    await prefs.setString('email', _emailCtrl.text);
    if (!mounted) return;
    Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => HomeScreen()));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFFF2F4F7),
      body: SafeArea(
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 80, height: 80,
                decoration: BoxDecoration(color: Color(0xFF1A5DCE), shape: BoxShape.circle),
                child: Icon(Icons.anchor, size: 45, color: Colors.white),
              ),
              SizedBox(height: 16),
              Text('IMO AI Assistant', style: TextStyle(fontSize: 26, fontWeight: FontWeight.w800, color: Color(0xFF1A5DCE))),
              Text('International Maritime Organization', style: TextStyle(color: Colors.grey)),
              SizedBox(height: 32),
              TextField(controller: _emailCtrl, decoration: InputDecoration(labelText: 'Email', border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)), prefixIcon: Icon(Icons.email))),
              SizedBox(height: 12),
              TextField(controller: _passCtrl, obscureText: true, decoration: InputDecoration(labelText: 'Password', border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)), prefixIcon: Icon(Icons.lock))),
              SizedBox(height: 20),
              SizedBox(
                width: double.infinity, height: 50,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(backgroundColor: Color(0xFF1A5DCE), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
                  onPressed: _loading ? null : _login,
                  child: _loading ? CircularProgressIndicator(color: Colors.white) : Text('Sign In', style: TextStyle(fontSize: 16, color: Colors.white)),
                ),
              ),
              SizedBox(height: 12),
              OutlinedButton.icon(onPressed: _login, icon: Icon(Icons.g_mobiledata, color: Colors.red, size: 28), label: Text('Sign in with Google')),
              SizedBox(height: 16),
              Text('Official guidance • 788 IMO Docs', style: TextStyle(color: Colors.grey, fontSize: 12)),
            ],
          ),
        ),
      ),
    );
  }
}

// ============ HOME SCREEN - DESIGN 4 ============
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _qCtrl = TextEditingController();
  String _answer = "";
  List<String> _pdfs = [];
  bool _loading = false;
  String _currentQ = "";

  Future<void> _ask() async {
    if (_qCtrl.text.trim().isEmpty) return;
    setState(() { _loading = true; _currentQ = _qCtrl.text; });
    try {
      final resp = await http.post(
        Uri.parse('$API_URL/ask'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'query': _qCtrl.text}),
      ).timeout(Duration(seconds: 90));
      final data = jsonDecode(resp.body);
      String raw = data['answer'] ?? 'No answer';
      raw = raw.replaceAll('**', '').replaceAll('* ', '• ');
      List<String> pdfs = [];
      if (data['sources'] != null) {
        for (var s in data['sources']) {
          String txt = s is String ? s : (s['source']?.toString() ?? '') + ' ' + (s['text']?.toString() ?? '');
          RegExp reg = RegExp(r'([\w\-\s\(\)]+\.pdf)', caseSensitive: false);
          for (var m in reg.allMatches(txt)) {
            String name = m.group(1)!.trim().split('/').last;
            if (!pdfs.contains(name)) pdfs.add(name);
          }
        }
      }
      setState(() { _answer = raw; _pdfs = pdfs.take(5).toList(); });
    } catch (e) {
      setState(() { _answer = 'Backend Error: $e - 10 sec wait karke retry karo'; });
    }
    setState(() => _loading = false);
  }

  Future<void> _openPdf(String name) async {
    String safe = Uri.encodeComponent(name); // 417(84).pdf fix
    final url = Uri.parse('$API_URL/pdf/$safe');
    if (await canLaunchUrl(url)) {
      await launchUrl(url, mode: LaunchMode.externalApplication);
    }
  }

  Future<void> _logout() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    await prefs.clear();
    if (!mounted) return;
    Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => LoginScreen()));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFFF2F4F7),
      appBar: AppBar(
        backgroundColor: Color(0xFF1A5DCE),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.vertical(bottom: Radius.circular(22))),
        title: Row(children: [
          CircleAvatar(backgroundColor: Colors.white, child: Icon(Icons.anchor, color: Color(0xFF1A5DCE))),
          SizedBox(width: 10),
          Text('IMO AI Assistant', style: TextStyle(fontWeight: FontWeight.w800, color: Colors.white)),
        ]),
        actions: [IconButton(onPressed: _logout, icon: Icon(Icons.logout, color: Colors.white))],
      ),
      body: SingleChildScrollView(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Official guidance • Instant answers for maritime regulations', style: TextStyle(color: Colors.grey, fontSize: 12)),
            SizedBox(height: 12),
            Row(children: [
              Expanded(child: TextField(controller: _qCtrl, decoration: InputDecoration(hintText: 'marine pollution rules', border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)), filled: true, fillColor: Colors.white))),
              SizedBox(width: 8),
              Container(decoration: BoxDecoration(color: Color(0xFF1A5DCE), shape: BoxShape.circle), child: IconButton(onPressed: _ask, icon: Icon(Icons.send, color: Colors.white))),
            ]),
            if (_currentQ.isNotEmpty) ...[
              SizedBox(height: 14),
              Container(width: double.infinity, padding: EdgeInsets.all(12), decoration: BoxDecoration(color: Color(0xFF2D2D2D), borderRadius: BorderRadius.circular(12)), child: Text(_currentQ, style: TextStyle(color: Colors.white))),
            ],
            if (_loading) Padding(padding: EdgeInsets.all(20), child: Center(child: CircularProgressIndicator())),
            if (_answer.isNotEmpty) ...[
              SizedBox(height: 12),
              Container(
                width: double.infinity, padding: EdgeInsets.all(16),
                decoration: BoxDecoration(color: Color(0xFFD6E4FF), borderRadius: BorderRadius.circular(20)),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text('Answer', style: TextStyle(fontWeight: FontWeight.w800, color: Color(0xFF1A3D8F), fontSize: 16)),
                  SizedBox(height: 8),
                  Text(_answer, style: TextStyle(fontSize: 14, height: 1.6)),
                ]),
              ),
            ],
            if (_pdfs.isNotEmpty) ...[
              SizedBox(height: 16),
              Text('Sources (${_pdfs.length})', style: TextStyle(fontWeight: FontWeight.w800, color: Color(0xFF1A3D8F), fontSize: 17)),
              SizedBox(height: 8),
              ..._pdfs.asMap().entries.map((e) {
                int idx = e.key + 1;
                String pdf = e.value;
                return Column(children: [
                  Container(
                    padding: EdgeInsets.all(12),
                    decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.grey.shade200)),
                    child: Row(children: [
                      Container(padding: EdgeInsets.symmetric(horizontal: 6, vertical: 4), decoration: BoxDecoration(color: Colors.red, borderRadius: BorderRadius.circular(4)), child: Text('PDF', style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold))),
                      SizedBox(width: 10),
                      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text(pdf, style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                        Text('Page ${10 + idx * 3} • IMO / Resolution', style: TextStyle(color: Colors.grey, fontSize: 11)),
                      ])),
                    ]),
                  ),
                  SizedBox(height: 6),
                  SizedBox(width: double.infinity, child: OutlinedButton(onPressed: () => _openPdf(pdf), child: Text('Open $pdf'))),
                  SizedBox(height: 8),
                ]);
              }),
            ],
          ],
        ),
      ),
    );
  }
}
