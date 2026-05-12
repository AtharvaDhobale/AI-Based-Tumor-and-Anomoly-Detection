## API examples (curl)

Assumes backend at `http://localhost:8000`.

### Register

```bash
curl -sS -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"doctor@example.com","full_name":"Dr. Example","password":"password123"}'
```

### Login

```bash
TOKEN=$(curl -sS -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"doctor@example.com","password":"password123"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo $TOKEN
```

### Upload MRI

```bash
curl -sS -X POST http://localhost:8000/api/mri/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "patient_id=P001" \
  -F "file=@sample.png"
```

### Detect

```bash
curl -sS -X POST http://localhost:8000/api/mri/detect/1 \
  -H "Authorization: Bearer $TOKEN"
```

