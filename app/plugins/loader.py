"""Dynamic router loader - enables plug-and-play module loading"""
import importlib
import pkgutil
from pathlib import Path
from fastapi import FastAPI
from typing import List
from ..core.logging import logger


class PluginLoader:
    """Dynamically load and register routers from modules"""
    
    @staticmethod
    def load_routers(app: FastAPI, modules_path: str = "app.modules") -> List[str]:
        """
        Dynamically load all routers from modules package
        
        Args:
            app: FastAPI application instance
            modules_path: Path to modules package
            
        Returns:
            List of loaded module names
        """
        loaded_modules = []
        
        try:
            modules_package = importlib.import_module(modules_path)
            
            # Iterate through all submodules
            for importer, module_name, ispkg in pkgutil.iter_modules(modules_package.__path__):
                if ispkg:  # Only process packages
                    try:
                        # Import the module
                        full_module_name = f"{modules_path}.{module_name}"
                        module = importlib.import_module(full_module_name)
                        
                        # Try to load routes
                        if hasattr(module, "routes"):
                            routes_module = importlib.import_module(f"{full_module_name}.routes")
                            if hasattr(routes_module, "router"):
                                app.include_router(routes_module.router)
                                loaded_modules.append(module_name)
                                logger.info(f"Loaded router from module: {module_name}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to load routes from {module_name}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error loading plugins: {str(e)}")
        
        return loaded_modules
    
    @staticmethod
    def load_custom_router(app: FastAPI, router_path: str, prefix: str = ""):
        """
        Load a specific router from a custom location
        
        Args:
            app: FastAPI application instance
            router_path: Path to router module (e.g., "app.modules.custom.routes")
            prefix: Optional path prefix for the router
        """
        try:
            routes_module = importlib.import_module(router_path)
            if hasattr(routes_module, "router"):
                router = routes_module.router
                if prefix:
                    router.prefix = prefix
                app.include_router(router)
                logger.info(f"Loaded custom router from: {router_path}")
            else:
                logger.warning(f"No 'router' object found in {router_path}")
        except Exception as e:
            logger.error(f"Failed to load custom router {router_path}: {str(e)}")
