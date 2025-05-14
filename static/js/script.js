// 🔄 Crear un nuevo registro
async function createRecord(nombre, edad, carrera_id) {
    const response = await fetch('/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nombre, edad, carrera_id })
    });
    const result = await response.json();
    console.log('CREATE:', result);
    return result;
}

// ✏️ Actualizar un registro
async function updateRecord(id, nombre, edad, carrera_id, transactionLevel = "NO TRANSACTION") {
    const response = await fetch(`/update/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nombre, edad, carrera_id, transactionLevel })
    });
    const result = await response.json();
    console.log('UPDATE:', result);
    return result;
}

// 🗑️ Eliminar un registro
async function deleteRecord(id) {
    const response = await fetch(`/delete/${id}`, { method: 'DELETE' });
    const result = await response.json();
    console.log('DELETE:', result);
    return result;
}

// 🔍 Obtener todos los registros
async function fetchAllRecords() {
    const response = await fetch('/read');
    const result = await response.json();
    console.log('READ ALL:', result);
    return result;
}

// 🔎 Obtener un registro por ID
async function fetchRecordById(id) {
    const response = await fetch(`/read/${id}`);
    if (response.ok) {
        const result = await response.json();
        console.log(`READ ${id}:`, result);
        return result;
    } else {
        const error = await response.json();
        console.error(`Error al leer registro ${id}:`, error.message);
        return null;
    }
}
